"""
CVS reader that provides:
- doi lookup
- pid lookup

NOT USED FOR MERGED DATA? shouldn't matter, should it?

"""

import os, sys, json
from csv_reader import CsvRecord, CsvReader
from filtering_cvs_reader import FilteringCsvReader

# sys.path.append('/Users/ostwald/devel/projects/library-admin')
# from ncarlibadmin import CONFIG
# from ncarlibadmin.batch import feed as feeds
# from ncarlibadmin.islandora_client import get_utc_time


class AwardIdDatasetRecord(CsvRecord):

    def __init__ (self, data, schema):
        CsvRecord.__init__(self, data, schema)

    def __repr__ (self):
        s = ""
        for field in self.schema:
            s += '\n- {}: {}'.format(field, self[field])
        return s

# class AwardIdDatasetReader(CsvReader):
class AwardIdDatasetReader(FilteringCsvReader):

    """
    Extends filtering
    """
    record_class = AwardIdDatasetRecord

    # def __init__ (self, path):
    def __init__ (self, path, filter_args={}, sort_args={}):
        self.path = path
        self.dup_pids = {}
        self.dup_dois = {}
        self.name = os.path.basename(self.path)

        # CsvReader.__init__ (self, path)
        FilteringCsvReader.__init__ (self, path, filter_args, sort_args)

        self.pid_map = {}
        self.doi_map = {}

        for rec in self.data:
            if self.pid_map.has_key(rec['pid']):
                pid = rec['pid']
                if self.dup_pids.has_key(pid):
                    vals = [self.pid_map[pid],]
                else:
                    # raise Exception, 'I dnnt think so'
                    vals = self.dup_pids.has_key(pid) and self.dup_pids[pid] or []
                vals.append(rec['doi'])
                self.dup_pids[pid] = vals
            else:
                self.pid_map[rec['pid']] = rec

            if self.doi_map.has_key(rec['doi']):
                doi = rec['doi']
                if self.doi_map.has_key(doi):
                    vals = [self.doi_map[doi]['pid'],]
                else:
                    vals = self.dup_dois.has_key(doi) and self.dup_dois[doi] or []
                vals.append(rec['pid'])
                self.dup_dois[doi] = vals
            else:
                self.doi_map[rec['doi']] = rec

    def get_recs_having_award_id(self):
        return filter (lambda x:len(x['kuali_verified_award_ids'].strip()) > 0 , self.data)

    def get_unique_award_ids (self):
        recs_with_award_id = self.get_recs_having_award_id()
        award_ids = []
        for rec in recs_with_award_id:
            ids = rec['kuali_verified_award_ids'].split(',')
            award_ids += ids
        return list(set(award_ids))

if __name__ == '__main__':
    comp_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_id_data-Composite.csv'
    partial_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL_v2.csv'
    doi_ref_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv'

    filter_args = {'start':'2020-01-01', 'end':'2020-02-01'}
    sort_args = {'field':'pid'}

    reader = AwardIdDatasetReader(comp_path)
    print 'reader has {}'.format(len(reader.data))
    if 1:
        dois = reader.doi_map.keys()
        print '{} dois'.format(len(dois))
        out_path = os.path.join (os.path.dirname(reader.path), 'OPENSKY_DOIS.txt')
        fp = open(out_path, 'w')
        fp.write ('\n'.join (dois))
        fp.close()
        print 'wrote to {}'.format(out_path)


    # print 'reader has {} objects'.format(len(reader.data))
    # recs_with_award_id = reader.get_recs_having_award_id()
    # print '{} with award_id'.format(len(recs_with_award_id))
    #
    # unique_award_ids = reader.get_unique_award_ids()
    # print '{} unique award_ids'.format(len(unique_award_ids))
    # for id in unique_award_ids:
    #     print id


