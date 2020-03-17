"""
Award_id table has the following columns
[pid, doi, award_ids]

Compare to award_id tables to see which award_ids have been assigned
to records previously, and by Kuali verification


"""
import os, sys, re, codecs
from lxml import etree as ET
sys.path.append ('/Users/ostwald/devel/projects/library-utils')
from ncarlibutils.fedora import CONFIG, get_datastream, update_datastream

from ncarlibadmin.model.fedora import FedoraObject
from ncarlibadmin.model.mods import MODS

sys.path.append ('/Users/ostwald/devel/opensky/pubs_to_grants/python')
from csv_processor import CsvReader, CsvRecord



class Award_ID_Record (CsvRecord):

    def __init__ (self, data, schema):
        CsvRecord.__init__ (self, data, schema)

        self.award_ids = self.get_award_ids()

    def get_award_ids(self):
        ids = self['award_ids'].split(',')
        ids = map (lambda x:x.strip(), ids)
        ids = filter (lambda x: len(x)>0, ids)
        ids.sort()
        return ids

class Award_ID_Table (CsvReader):
    record_class = Award_ID_Record
    dowrites = 0

    def __init__ (self, path):
        self._pid_map = None
        CsvReader.__init__ (self, path)


    def get_pid_map (self):
        if self._pid_map is None:
            self._pid_map = {}
            for rec in self.data:
                self._pid_map[rec['pid']] = rec

        return self._pid_map

    def get_pids (self):

        # print 'get_pids: {}'.format(len(self.data))
        # print self.data[0].schema
        #
        # pids = map (lambda x:x['pid'], self.data)
        pids = self.get_pid_map().keys()
        pids.sort()
        return pids

    def get_rec(self, pid):
        return self.get_pid_map()[pid]



if __name__ == '__main__':

    print 50*'-'
    print 'Fedora server:', CONFIG.get("fedora", "SERVER")

    if 1:
        base_dir = '/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/'
        # kuali_path = os.path.join (base_dir, 'KUALI_TRIAL_RECS.csv')
        kuali_path = os.path.join (base_dir, 'KUALI_FILTERED_TRIAL_RECS.csv')
        kuali_table = Award_ID_Table(kuali_path)
        print '{} recs read from {}'.format(len(kuali_table.data), kuali_path)

        kuali_pids = kuali_table.get_pids()


        old_path = os.path.join (base_dir, 'FUNDING_REPORTER_OUTPUT.csv')
        # old_path = os.path.join (base_dir, '/Users/ostwald/tmp/Book2.csv')
        old_table = Award_ID_Table(old_path)
        print '{} recs read from {}'.format(len(old_table.data), old_path)

        old_pids = old_table.get_pids()

        already_done_old = []
        for pid in old_pids:
            if pid in kuali_pids:
                already_done_old.append(pid)

        print '{} curent records with finder data, also have kuali data'.format(len (already_done_old))
        for pid in already_done_old:
            print '-', pid
            old_award_ids = old_table.get_rec(pid).get_award_ids()
            print '  - old: {}'.format(old_award_ids)
            kuali_award_ids = kuali_table.get_rec(pid).get_award_ids()
            print '  - kuali: {}'.format(kuali_award_ids)

        already_done_kuali = []
        for pid in kuali_pids:
            if pid in old_pids:
                already_done_kuali.append(pid)

        # for pid in already_done_kuali:
        #     old_award_ids = old_table.get_rec(pid).get_award_ids()
            # print '-', pid
            # print '  - old: {}'.format(old_award_ids)
            # kuali_award_ids = kuali_table.get_rec(pid).get_award_ids()
            # print '  - kuali: {}'.format(kuali_award_ids)

        # print 'in kuali ids but not in old ids'
        # for pid in already_done_kuali:
        #     if not pid in already_done_old:
        #         print ' - {}'.format(pid)