"""
sync the opensky metadata with values from Cached_Award_Data.csv

Traverse DOI-REFERENCE_TABLE.csv table. for each record compare the award_ids with
Cached_Award_Data validated_award_ids for that record.
- If reference award_ids include a skip_award_id, remove it.
- If a validated_award_id is not present in the reference, then add it.

We are not worried about legacy award ids here, these are dealt with in legacy_sync ....
"""

import os, sys, re, time
sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')

import json
from csv_processor import CsvRecord, CsvReader
from UserDict import UserDict
from back_fill import NotesMODS
from kuali_cache import KualiCache


from ncarlibutils.fedora import CONFIG
from ncarlibadmin.islandora_client import IslandoraObject
from ncarlibadmin.batch import clean_mods
from lxml import etree as ET

XSLT_CLEAN_PATH = '/Users/ostwald/devel/projects/library-admin/ncarlibadmin/batch/job/fall_2016/xslt/cleanup.xsl'

class AwardIdRecord (CsvRecord):
    """
    Extends CsvRecord - exposes pid and ids
    """
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
    """
    Extends CsvReader to build:
    - pid_map - maps pids to the award_ids they contain
    - rec_map - maps pids to their records (AwardIdRecord instances)

    provides:
    - get_rec (pid)
    - git_ids (pid)
    """
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

class CurrentAwardIdsRecord (AwardIdRecord):
    award_id_column = 'award_ids'

class CurrentAwardIdsTable (AwardIdTable):
    record_class = CurrentAwardIdsRecord

class CacheRecord (AwardIdRecord):
    award_id_column = 'validated_award_ids'

class CacheTable (AwardIdTable):
    record_class = CacheRecord

class Synchonizer:
    """
    CurrentAwardIdsTable (read from provided ref_csv). Contains current award_id assignments
    CacheTable (read from provided cache_csv). Contains cached award_id assignments
    """
    dowrites = 0
    verbose = 1
    kuali_award_selector = '/mods:mods/mods:note[@type="funding" and not(@displayLabel)]'

    def __init__(self, ref_csv, cache_csv):
        self.ref_table = CurrentAwardIdsTable (ref_csv)
        self.cache_table = CacheTable (cache_csv)
        self.kuali_cache = KualiCache()

    def do_sync (self):
        pids = self.ref_table.pid_map.keys()
        pids.sort()
        for pid in pids:
            self.sync_pid(pid)
            # print pid

    def sync_pid (self, pid):
        ref_ids = self.ref_table.pid_map[pid] # ref_ids are what are currently in the record
        if not self.cache_table.pid_map.has_key(pid):
            cache_ids = []
        else:
            cache_ids = self.cache_table.pid_map[pid]
        all_ids = ref_ids + cache_ids

        # kuali_ids are all kuali-verified but may contain dupes
        kuali_ids = filter (None, map (lambda x:self.kuali_cache.find_kuali_id(x), all_ids))

        # target_award_ids have no dups - these are the ids we want in the record
        target_award_ids = list(set(kuali_ids))

        if sorted(target_award_ids) == sorted(ref_ids):
            if self.verbose:
                print '\n{} - no change'.format(pid)
            return

        if self.verbose:
            print '\n{}'.format(pid)
            print ' - ref_ids: {}'.format(ref_ids)
            print ' - cache_ids: {}'.format(cache_ids)
            print ' - TARGET_ids: {}'.format(target_award_ids)

        islandora_object = IslandoraObject(pid)
        mods = islandora_object.get_mods_record()

        # safe guard against processing a record twice ....
        # existing_award_ids = mods.getValuesAtPath('/mods:mods/mods:note[@type="funding" and not @displayLabel]')
        existing_award_ids = mods.getValuesAtPath(self.kuali_award_selector)
        print 'existing_award_ids:', existing_award_ids
        if sorted(target_award_ids) == sorted(existing_award_ids):
            print '\n{} - record already processed'.format(pid)
            return

        self.backup_obj(pid, str(mods))

        for award_id in target_award_ids:
            if not award_id in ref_ids:
                # add this award_id
                self.add_award_id_to_mods(award_id, mods)
        for award_id in ref_ids:
            if not award_id in kuali_ids:
                # remove this award_id
                self.remove_award_id_from_mods (award_id, mods)

        self.remove_dup_award_ids(mods)

        cleaned_mods = clean_mods(mods.dom, XSLT_CLEAN_PATH)
        mods_xml = ET.tostring(cleaned_mods, pretty_print=1, encoding='utf8')

        if self.dowrites:
            islandora_object.put_mods_datastream (mods_xml)
            print '- updated', pid
            time.sleep(.5)
        else:
            print '- woulda updated', pid
            # print mods_xml

    def remove_dup_award_ids(self, mods):
        seen_ids = []
        award_id_nodes = mods.selectNodesAtPath(self.kuali_award_selector)
        for node in award_id_nodes:
            award_id = node.text
            if award_id in seen_ids:
                node.getparent().remove(node)
            else:
                seen_ids.append(award_id)

    def add_award_id_to_mods(self, award_id, mods):
        # print '- adding', award_id
        #  create the funding note for mods
        new_note_name = '{%s}%s' % (mods.namespaces['mods'], 'note')
        new_note = ET.Element(new_note_name)
        new_note.set('type', 'funding')
        new_note.text = award_id

        # insert it in mods doc
        funding_notes = mods.selectNodesAtPath('/mods:mods/mods:note[@type="funding"]')
        if len(funding_notes) > 0:
            mods.dom.insert(mods.dom.index(funding_notes[-1])+1, new_note)
            # print ' - inserted ', award_id
        else:
            mods.dom.append(new_note)
            # print ' - appended ', award_id

    def remove_award_id_from_mods(self, award_id, mods):
        # print 'removing', award_id
        funding_notes = mods.selectNodesAtPath(self.kuali_award_selector)
        for node in funding_notes:
            if node.text == award_id:
                node.getparent().remove(node)
                # print ' - removed', award_id


    def backup_obj (self, pid, mods):
        path = self.get_backup_path(pid)
        if not os.path.exists(path):
            fp = open(path, 'w')
            fp.write (mods)

    def get_backup_path(self, pid):
        backupdir = '/Users/ostwald/tmp/pre_sync_backup'
        if not os.path.exists(backupdir):
            os.mkdir (backupdir)
        filename = pid.replace (':', '_') + '.xml'
        return os.path.join (backupdir, filename)

if __name__ == '__main__':
    ref_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    ref_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-LEGACY-REFERENCE_TABLE.csv'
    # cache_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Cached_Award_Data.csv'
    cache_data = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL.csv'

    sync = Synchonizer(ref_data, cache_data)

    if 1:
        sync.do_sync()

    if 0: # script tester
        pid = 'articles:19755'
        # pid = 'articles:18702'
        # pid = 'articles:22287'
        # pid = 'articles:22993'
        # pid = 'articles:24651'
        sync.sync_pid (pid)


