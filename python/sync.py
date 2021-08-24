"""
sync the opensky metadata with values from Cached_Award_Data.csv

Traverse DOI-REFERENCE_TABLE.csv table. for each record compare the award_ids with
Cached_Award_Data validated_award_ids for that record.
- If reference award_ids include a skip_award_id, remove it.
- If a validated_award_id is not present in the reference, then add it.

We are not worried about legacy award ids here, but these must also be dealt with ....
"""

import os, sys, re, time
import json
from csv_processor import CsvRecord, CsvReader
from UserDict import UserDict
from back_fill import NotesMODS

sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibutils.fedora import CONFIG
from ncarlibadmin.islandora_client import IslandoraObject
from ncarlibadmin.batch import clean_mods
from lxml import etree as ET

XSLT_CLEAN_PATH = '/Users/ostwald/devel/projects/library-admin/ncarlibadmin/batch/job/fall_2016/xslt/cleanup.xsl'

class AwardIdRecord (CsvRecord):
    award_id_column = ''

    def __init__ (self, data, schema):
        CsvRecord.__init__(self, data, schema)
        self.pid = self['pid']
        self.ids = self.get_award_ids()

    def get_award_ids (self):
        ids = filter (None, self[self.award_id_column].split(','))
        ids = map (lambda x:x.strip(), ids)
        ids.sort()
        return ids

    def __repr__ (self):
        return ', '.join(self.data)


class AwardIdTable (CsvReader):
    record_class = AwardIdRecord

    def __init__ (self, path):
        CsvReader.__init__(self, path)
        self.pid_map = UserDict()
        self.rec_map = UserDict()

        for rec in self.data:
            self.pid_map[rec.pid] = rec.ids
            self.rec_map[rec.pid] = rec

    def get_rec(self, pid):
        return self.rec_map[pid]

    def get_ids(self, pid):
        return self.pid_map[pid]

class RefRecord (AwardIdRecord):
    award_id_column = 'award_ids'

class RefTable (AwardIdTable):
    record_class = RefRecord

class CacheRecord (AwardIdRecord):
    award_id_column = 'validated_award_ids'

class CacheTable (AwardIdTable):
    record_class = CacheRecord

class Synchonizer:

    dowrites = 1

    def __init__(self, ref_data, cache_data):
        self.ref_table = RefTable (ref_data)
        self.cache_table = CacheTable (cache_data)

    def report(self):
        for pid in self.ref_table.pid_map.keys():
            ref_ids = self.ref_table.pid_map[pid]
            if not self.cache_table.pid_map.has_key(pid):
                continue
            cache_ids = self.cache_table.pid_map[pid]

            if set(ref_ids) == set(cache_ids):
                continue

            print '-{} - ref: {},  cache: {}'.format(pid, ref_ids, cache_ids)

            # if '1852977' in cache_ids and not '1852977' in ref_ids:
            #     print ' -- add 1852977'

            for cache_id in cache_ids:
                if cache_id in ref_ids:
                    continue
                elif len(ref_ids) == 0:
                    print ' -- add', cache_id
                    continue
                else:
                    found = 0
                    for ref_id in ref_ids:
                        if cache_id.endswith(ref_id[-5:]) and ref_id != cache_id:
                            print ' -- replace {} with {}'.format(ref_id, cache_id)
                            found = 1
                            break
                    if not found:
                        print ' -- add', cache_id
                        pass

    def get_sync_script(self, verbose=0):
        """
        json looks like this:
        [
            {
                pid: {
                    ref_ids: [],
                    cache_ids: [],
                    ops: [
                        { 'op' : 'add', 'award_id' :'asdsafd'},
                        {'op': 'replace', 'old' : 'adsfasf',  'new' : 'asdfsaddd'}
                    ]
                },
            ...
        ]
        :return:
        """
        script = []
        for pid in self.ref_table.pid_map.keys():
            ref_ids = self.ref_table.pid_map[pid]
            if not self.cache_table.pid_map.has_key(pid):
                continue
            cache_ids = self.cache_table.pid_map[pid]

            if set(ref_ids) == set(cache_ids):
                continue
            if verbose:
                print '-{} - ref: {},  cache: {}'.format(pid, ref_ids, cache_ids)

            pid_item = {
                'pid':pid,
                'ref_ids': ref_ids,
                'cache_ids': cache_ids,
                'ops' : []
            }

            script.append(pid_item)
            # if '1852977' in cache_ids and not '1852977' in ref_ids:
            #     print ' -- add 1852977'

            pid_ops = pid_item['ops']
            for cache_id in cache_ids:
                if cache_id in ref_ids:
                    continue
                elif len(ref_ids) == 0:
                    if verbose:
                        print ' -- add', cache_id
                    pid_ops.append ({'op' : 'add', 'award_id' : cache_id})
                    continue
                else:
                    found = 0
                    for ref_id in ref_ids:
                        if cache_id.endswith(ref_id[-5:]) and ref_id != cache_id:
                            if verbose:
                                print ' -- replace {} with {}'.format(ref_id, cache_id)
                            pid_ops.append ({'op' : 'replace', 'old':ref_id, 'new': cache_id})
                            found = 1
                            break
                    if not found:
                        if verbose:
                            print ' -- add', cache_id
                        pid_ops.append ({'op':'add', 'award_id' : cache_id})
        return script

    def do_sync(self):
        max = 10000
        sync_script = self.get_sync_script()
        for i, item in enumerate(sync_script):
            if i > 0 and i % 100 == 0:
                print '{}/{}'.format(i, len(sync_script))
            pid = item['pid']
            if i >= max:
                break
            print '\n', pid
            ops = item['ops']
            if len(ops) == 0:
                print '- skipping because there are no ops ...'
                continue
            if os.path.exists(self.get_backup_path(pid)):
                print '- already synced'
            else:
                self.sync_object(pid, ops)


    def sync_object (self, pid, ops):
        obj = IslandoraObject (pid)
        # print obj.get_mods_datastream()
        mods = NotesMODS(obj.get_mods_datastream(), pid)
        backup_mods_xml = str(mods)

        for action in ops:
            op = action['op']
            if op == 'add':
                award_id = action['award_id']
                verified_ids = map (lambda x:x.text, mods.get_funding_notes(True))
                if award_id in verified_ids:
                    print '- add: {} already exists'.format(award_id)
                    continue
                mods.add_funding_note (award_id)

            if op == 'replace':
                new_id = action['new']
                verified_ids = map (lambda x:x.text, mods.get_funding_notes(True))
                if new_id in verified_ids:
                    print '- replace: {} already exists'.format(new_id)
                else:
                    mods.add_funding_note(new_id)
                mods.remove_funding_note(action['old'])

        if self.dowrites:
            mods_tree = clean_mods(mods.dom, XSLT_CLEAN_PATH)
            obj.put_mods_datastream (ET.tostring(mods_tree, pretty_print=1))
            self.backup_obj(pid, backup_mods_xml)
            print 'updated', pid
            time.sleep(0.95)
        else:
            print pid, 'verified award_ids after update'
            print map(lambda x:x.text, mods.get_funding_notes('verified_only'))

    def backup_obj (self, pid, mods):

        fp = open(self.get_backup_path(pid), 'w')
        fp.write (mods)

    def get_backup_path(self, pid):
        backupdir = '/Users/ostwald/tmp/pubs_to_grants_backups'
        filename = pid.replace (':', '_') + '.xml'
        return os.path.join (backupdir, filename)

if __name__ == '__main__':
    ref_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    cache_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Cached_Award_Data.csv'

    sync = Synchonizer(ref_data, cache_data)
    print sync.report()
    # print json.dumps (sync.get_sync_script(), indent=2)
    # sync.do_sync()




    # print json.dumps(script, indent=2)

    if 1: # script tester
        pid = 'articles:22652'
        ops = [
            {'op': 'add', 'award_id' : '1755088'},
            # {'op': 'replace', 'old' : 'DESC0016476', 'new': 'DE-SC0016476'},
            # {'op': 'replace', 'old' : 'DESC0020104', 'new': 'DE-SC0020104'}
        ]

        sync.sync_object (pid, ops)


