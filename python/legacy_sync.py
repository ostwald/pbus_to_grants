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
    - else
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
from kuali_cache import KualiCache

from ncarlibutils.fedora import CONFIG
from ncarlibadmin.islandora_client import IslandoraObject
from ncarlibadmin.batch import clean_mods
import ncarlibadmin.batch.feed as feeds
from lxml import etree as ET

XSLT_CLEAN_PATH = '/Users/ostwald/devel/projects/library-admin/ncarlibadmin/batch/job/fall_2016/xslt/cleanup.xsl'
LEGACY_FUNDER_PAT = re.compile('.*?:(.*)')  #  abbrev ignored
SANITIZE_PAT = re.compile('[^A-Za-z0-9 ]')
TOKEN_PAT = re.compile('[\d]')

SKIP_IDS = [  # see https://stage.ucar.dgicloud.com/admin/config/system/openskydora
    '999999',
    'DEAC0576L01830',
    'DEAC0576RL01830',
    'DEAC5207NA27344',
    'DEAC0500OR22725',
    'DEAC3608GO28308',
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
        self.kuali_cache = KualiCache ()
        CsvReader.__init__(self, path)
        self.pid_map = UserDict()

        for rec in self.data:
            self.pid_map[rec.pid] = rec

    def get_record (self, pid):
        return self.pid_map[pid]

    def get_unique_legacy_award_ids(self):
        all_ids = []
        for rec in self.data:
            legacy_ids = map (LegacyAwardId, rec.legacy_award_ids)
            for id in legacy_ids:
                all_ids += id.tokens
        # print 'all_ids is a {}'.format(type(all_ids))
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
        if 0: # we don't want to maintain the kuali_client
            return self.kuali_client.get_kuali_award_id(award_id)
        if 1: # use cached
            return self.kuali_cache.find_kuali_id(award_id)

    def backup_obj (self, pid, mods):
        path = self.get_backup_path(pid)
        if os.path.exists(path):
            print 'backup already exists at ', path
            return
        fp = open(self.get_backup_path(pid), 'w')
        fp.write (mods)
        fp.close()

    def get_backup_path(self, pid):
        backupdir = '/Users/ostwald/tmp/pubs_to_grants_legacy_sinc_backups'
        if not os.path.exists(backupdir):
            os.mkdir(backupdir)
        filename = pid.replace (':', '_') + '.xml'
        return os.path.join (backupdir, filename)

    def do_sync(self):
        for record in self.data:
            self.sync_record (record)
        print 'sync is complete'

    def get_unknown_legacy_ids(self):
        """
        :return: a list if legacy id tokens unknown to kuali_cache
        """
        unique_legacy_ids = self.get_unique_legacy_award_ids()
        keys = self.kuali_cache.keys()
        unknown_ids = [];add = unknown_ids.append
        for id in unique_legacy_ids:
            try:
                id = u(id)
            except:
                pass
            if not id in keys:
                add (id)
        return unknown_ids

    def write_unknown_legacy_ids(self, outpath='/Users/ostwald/tmp/UNKNOWN_LEGACIES.txt'):
        unknown_ids = self.get_unknown_legacy_ids()
        fp = open(outpath, 'w')
        fp.write ('\n'.join(unknown_ids))
        fp.close()
        print 'wrote to', outpath

    def sync_record(self, record):
        pid = record['pid']
        legacy_ids = map (LegacyAwardId, record.legacy_award_ids)
        for id in legacy_ids:
            # print id.tokens
            # use the info in the spreadsheet to indidate whether there are kualified legacy ids
            kualified_legacy_ids = filter (None, map (lambda x:self.kuali_cache.find_kuali_id(x), id.tokens))
            if len(kualified_legacy_ids) > 0:
                print '{} - award_ids: {}, kualified_legacy_ids: {}'.format(pid, record.award_ids, kualified_legacy_ids)

                """
                now that we know there are kualified ids (and this MODS must be modified),
                for each legacy id
                    if we can make any of the tokens into a Kuali_id
                    - remove the legacy id element
                    - if the kuali_id isn't in "award_ids" insert it as kuali_id
                    if any of the tokens are a skip_id
                    - remove the legacy id element
                """
                islandora_object = IslandoraObject (pid)
                # print islandora_object.get_mods_datastream()
                legacy_award_selector = '/mods:mods/mods:note[@type="funding" and @displayLabel]'
                mods = islandora_object.get_mods_record()
                backup_mods_xml = str(mods)
                object_changed = False
                legacy_id_nodes = mods.selectNodesAtPath(legacy_award_selector)
                print '- {} legacy_id_nodes found'.format(len(legacy_id_nodes))
                for node in legacy_id_nodes:
                    legacy_id = LegacyAwardId(node.text)
                    tokens = legacy_id.tokens
                    print '-- {}: {}'.format(legacy_id.raw, tokens)
                    for token in tokens:
                        kuali_id = self.kuali_cache.find_kuali_id(token)
                        if kuali_id:
                            if kuali_id in SKIP_IDS or kuali_id in record.award_ids:
                                node.getparent().remove(node)
                                object_changed = True
                                print ' --- deleted'
                                break # go on to next node
                            else:  # change this legacy award node to a kuali_id
                                del(node.attrib['displayLabel'])
                                node.text = kuali_id
                                object_changed = True
                                print ' --- converted legacy to kuali_id'
                                break
                if object_changed:
                    #  cleanup
                    cleaned_mods = clean_mods(mods.dom, XSLT_CLEAN_PATH)
                    mods_xml = ET.tostring(cleaned_mods, pretty_print=1, encoding='utf8')
                    if self.dowrites:
                        self.backup_obj (pid, backup_mods_xml)

                        islandora_object.put_mods_datastream (mods_xml)
                        print '- updated', pid
                        time.sleep(.5)
                    else:
                        print '- woulda updated', pid





def make_legacy_award_id_map(syncer):
    uniques = syncer.get_unique_legacy_award_ids()
    print len(uniques), 'uniques'
    for award_id in uniques:
        kuali_id = syncer.get_kuali_id(award_id)
        print '"{}" : "{}",'.format(award_id, kuali_id)


if __name__ == '__main__':
    path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-LEGACY-REFERENCE_TABLE.csv'
    syncer = LegacyAwardIdTable (path)

    syncer.do_sync()

    if 0: # unique legacy ids
        unique_tokens = syncer.get_unique_legacy_award_ids()
        skip_shorts = map (lambda x:x[-5:], SKIP_IDS)
        for id in unique_tokens:
            if id[-5:] in skip_shorts:
                print '{}'.format(id)


    if 0:
        pid = 'articles:14251'
        pid = 'articles:17548'
        pid = 'articles:22993'
        # pid = 'articles:20853'
        record = syncer.get_record(pid)
        syncer.sync_record(record)