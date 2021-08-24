"""
There are many award_ids marked as "legacy" when they shouldn't be.
The award_ids in many of these cases are not kuali-normalized either.

So the purpose of this module is to consume a csv that has (at least) the fields:
pid, award_ids, legacy_award_ids

for each pid we want to
- obtain a list of award_ids
    some of the values are verbose (e.g., "National Aeronautics and Space Administration (NASA): NNG06GB27G")
    use functionality from back_fill to get the testable id (e.g., "NNG06GB27G")
    - if it a skip award_id, remove legacy id element
    - get kuali-verified award_id
    - if legacy award_id is a kuali-verified value
        add to metadata if it is not there already
        remove the legacy element

so for each legacy award_id here are the possible operations:
- add verified id
- remove legacy id element

"""
import os, sys, re, time
import json
from csv_processor import CsvRecord, CsvReader
from UserDict import UserDict
from back_fill import NotesMODS
from python.client import KualiClient
from legacy_award_id_cache import LEGACY_AWARD_CACHE

sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibutils.fedora import CONFIG
from ncarlibadmin.islandora_client import IslandoraObject
from ncarlibadmin.batch import clean_mods
from lxml import etree as ET

XSLT_CLEAN_PATH = '/Users/ostwald/devel/projects/library-admin/ncarlibadmin/batch/job/fall_2016/xslt/cleanup.xsl'
LEGACY_FUNDER_PAT = re.compile('.*?:(.*)')  #  abbrev ignored
SANITIZE_PAT = re.compile('[^A-Za-z0-9 ]')
TOKEN_PAT = re.compile('[\d]')
SKIP_IDS = [
   '01830', '99999'
]


class LegacyAwardId:

    def __init__(self, raw):
        self.raw = raw.strip()
        self.tokens = self._tokenize()


    def _tokenize(self):
        m = LEGACY_FUNDER_PAT.match(self.raw)
        if m:
            s =  m.group(1)
        else:
            s = self.raw
        # print 'extracted:', s

        def token_filter (t):
            return len(t) > 4 and TOKEN_PAT.search(t)

        # tokens = map (sanitize_id, s.split(' '))
        # print '\ntokens'
        # for t in tokens:
        #     print '-',t
        #
        # filtered_tokens = filter (token_filter, tokens)
        # print '\nfiltered'
        # for t in filtered_tokens:
        #     print '-',t

        return filter (token_filter,  map (sanitize_id, s.split(' ')))


class LegacyAwardIdRecord (CsvRecord):

    def __init__ (self, data, schema):
        CsvRecord.__init__(self, data, schema)
        self.pid = self['pid']
        self.award_ids = self.get_award_ids('award_ids')
        self.legacy_award_ids = self.get_award_ids('legacy_award_ids')

    def get_award_ids (self, column):
        ids = filter (None, self[column].split(','))
        ids = map (lambda x:x.strip(), ids)
        ids.sort()
        return ids

    def __repr__ (self):
        return ', '.join(self.data)

def extract_award_id (s):
    m = LEGACY_FUNDER_PAT.match(s)
    if m:
        return m.group(1).split(' ')[-1]
    else:
        return s

def sanitize_id (id):
    """
    Remove all chars that are not letters or numbers
    :param id:
    :return:
    """
    # print 'id: {} ({})'.format(id, type(id))
    return re.sub (SANITIZE_PAT, '', id)

class LegacyAwardIdTable (CsvReader):
    """
    WE know that all ids in the award_id column are verified kuali IDs ...

    create a sync script from the LEGACY-AWARD_REFERENCE_TABLE.csv table

    use the script to update MODS record as necessary

    """
    record_class = LegacyAwardIdRecord
    dowrites = 1

    def __init__ (self, path):
        self.kuali_client = KualiClient()

        CsvReader.__init__(self, path)
        self.pid_map = UserDict()

        for rec in self.data:
            self.pid_map[rec.pid] = rec

    def get_unique_legacy_award_ids(self):
        all_ids = []
        for rec in self.data:
            legacy_ids = map (LegacyAwardId, rec.legacy_award_ids)
            for id in legacy_ids:
                all_ids += id.tokens
        print 'all_ids is a {}'.format(type(all_ids))
        all_set = set(all_ids)
        print 'there are {} uniques'.format(len(all_set))
        uniques = list(all_set)
        uniques.sort()
        return uniques

    def get_unique_kuali_award_ids(self):
        all_ids = []
        for rec in self.data:
            kuali_ids = filter (None, rec['award_ids'].split(','))
            if len(kuali_ids) < 1:
                continue
            # print kuali_ids
            all_ids += kuali_ids
        all_set = set(all_ids)
        print 'there are {} uniques'.format(len(all_set))
        uniques = list(all_set)
        uniques.sort()
        return uniques

    def get_kuali_id (self, award_id):
        return self.kuali_client.get_kuali_award_id(award_id)

    def get_sync_script(selfs, verbose=0):
        script = []
        for i, rec in enumerate(syncer.data):
            if verbose:
                print '\n', i+2
            pid = rec.pid
            # print pid
            object_sync_script = syncer.get_object_sync_script(pid, verbose=verbose)
            if verbose:
                print object_sync_script
            if len(object_sync_script['ops']) > 0:
                script.append(object_sync_script)

        return script

    def get_object_sync_script (self, pid, verbose=0):
        rec = self.pid_map[pid]
        validated_kuali_ids = rec['award_ids']

        legacy_id_objects = map (LegacyAwardId, rec['legacy_award_ids'].split(','))
        # print pid, rec.legacy_award_ids, rec['legacy_award_ids'].split(',')

        # print len(legacy_id_objects), 'legacy_id_objects'
        # return
        object_sync_script = {'pid' : pid, 'ops' : []}
        for i, legacy_id_obj in enumerate(legacy_id_objects):
            ids_from_tokens = [] # collect verified kuali ids
            if len(legacy_id_obj.tokens) > 0:
                if verbose:
                    print '{} - ({}) - {}'.format(pid, len(legacy_id_obj.tokens), legacy_id_obj.raw)

                for token in legacy_id_obj.tokens:
                    if not self.kuali_client.accept_award_id(token):
                        object_sync_script['ops'].append({'op':'remove', 'id':token})
                        continue
                    id = LEGACY_AWARD_CACHE[token]
                    if id is not None:
                        ids_from_tokens.append(id)

                if len(ids_from_tokens) == 0:
                    if verbose:
                        print 'Keep legacy_award_id - ', legacy_id_obj.raw

                if len(ids_from_tokens) > 1:
                    raise Exception, 'Mulitiple ids from tokens {}: {}'.format(pid, legacy_id_obj.raw)
                if len(ids_from_tokens) == 1:
                    kuali_id = ids_from_tokens[0]
                    # print '\n', pid
                    # print '{} - ({}) - {}'.format(pid, kuali_id, legacy_id_obj.raw)
                    if verbose:
                        print 'remove legacy_award_id - ', legacy_id_obj.raw
                    object_sync_script['ops'].append({'op' : 'remove', 'id' : legacy_id_obj.raw})

                    if not kuali_id in validated_kuali_ids:
                        if verbose:
                            print 'add award_id', kuali_id
                        object_sync_script['ops'].append({'op' : 'add', 'id' : kuali_id})
        return  object_sync_script

    def backup_obj (self, pid, mods):
        path = self.get_backup_path(pid)
        if os.path.exists(path):
            print 'backup already exists at ', path
            return
        fp = open(self.get_backup_path(pid), 'w')
        fp.write (mods)

    def get_backup_path(self, pid):
        backupdir = '/Users/ostwald/tmp/pubs_to_grants_legacy_sinc_backups'
        filename = pid.replace (':', '_') + '.xml'
        return os.path.join (backupdir, filename)

    def do_sync(self):
        sync_script = self.get_sync_script()
        for item in sync_script:
            pid = item['pid']
            print '\n-', pid
            if os.path.exists(self.get_backup_path(pid)):
                print 'already synced'
                continue
            ops = item['ops']
            self.sync_object(pid, ops)

        print 'sync is complete'

    def sync_object(self, pid, ops):
        obj = IslandoraObject (pid)
        # print obj.get_mods_datastream()
        mods = NotesMODS(obj.get_mods_datastream(), pid)
        backup_mods_xml = str(mods)
        object_changed = False

        for action in ops:
            op = action['op']
            if op == 'add':
                award_id = action['id']
                verified_ids = map (lambda x:x.text, mods.get_funding_notes(filter_spec='verified_only'))
                if award_id in verified_ids:
                    print '- add: {} already exists'.format(award_id)
                    continue
                mods.add_funding_note (award_id)
                object_changed = True

            if op == 'remove':
                legacy_id = action['id']
                print 'removing legacy id:', legacy_id
                legacy_ids = map (lambda x:x.text, mods.get_funding_notes(filter_spec='legacy_only'))
                if not legacy_id in legacy_ids:
                    print '- remove: {} already removed'.format(legacy_id)
                    continue
                mods.remove_funding_note(legacy_id, is_legacy=True)
                object_changed = True

        if object_changed:
            if self.dowrites:
                self.backup_obj(pid, backup_mods_xml)
                mods_tree = clean_mods(mods.dom, XSLT_CLEAN_PATH)
                obj.put_mods_datastream (ET.tostring(mods_tree, pretty_print=1))
                print 'updated', pid
                time.sleep(0.95)
            else:
                print pid, 'verified award_ids after update'
                print '- verified award_ids:', map(lambda x:x.text, mods.get_funding_notes('verified_only'))
                print '- legacy award_ids:\n - ', '\n - '.join(map(lambda x:x.text, mods.get_funding_notes('legacy_only')))
                # print mods
        else:
            print '{} not changed'.format(pid)

def make_legacy_award_id_map(syncer):
    uniques = syncer.get_unique_legacy_award_ids()
    print len(uniques), 'uniques'
    for award_id in uniques:
        kuali_id = syncer.get_kuali_id(award_id)
        print '"{}" : "{}",'.format(award_id, kuali_id)

def sync_tester(syncer):

    script_map = {}

    if 1:
        sync_script = syncer.get_sync_script()
        # print json.dumps(sync_script, indent=3)
        for item in sync_script:
            # print '\n', item['pid']
            # for op in item['ops']:
            #     print '-', op['op'], ':', op['id']
            script_map[item['pid']] = item['ops']

    if 1:
        pid = 'articles:17387'
        ops = script_map[pid]
        print json.dumps(ops, indent=2)
        syncer.sync_object(pid, ops)

if __name__ == '__main__':
    path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/LEGACY-AWARD_REFERENCE_TABLE.csv'
    syncer = LegacyAwardIdTable (path)

    # script = syncer.get_sync_script()
    # print json.dumps(script, indent=2)

    # sync_tester(syncer)
    syncer.do_sync()
    # make_legacy_award_id_map(syncer)


    # pid = 'articles:17006'
    # syncer.sync_object(pid)