"""
AwardIdDatasetReader - CVS reader that provides:
- doi lookup
- pid lookup

"""

import os, sys, json
from csv_reader import CsvRecord, CsvReader
from filtering_cvs_reader import FilteringCsvReader
from UserDict import UserDict
from kuali_cache import KualiCache

# sys.path.append('/Users/ostwald/devel/projects/library-admin')
# from ncarlibadmin import CONFIG
# from ncarlibadmin.batch import feed as feeds
# from ncarlibadmin.islandora_client import get_utc_time

class ListBucketDict(UserDict):
    """
    buckets are lists of items
    keys are sorted
    """
    def add (self, key, item):
        vals = self.data.has_key(key) and self.data[key] or []
        vals.append(item)
        self.data[key] = vals
            

class AwardIdDatasetRecord(CsvRecord):
    """
    Dates are in YYYY-MM-DD format
    """

    def __init__ (self, data, schema):
        CsvRecord.__init__(self, data, schema)

    def __repr__ (self):
        s = ""
        for field in self.schema:
            s += '\n- {}: {}'.format(field, self[field])
        return s

    def get_award_ids (self, column):
        """
        returns a list of award_ids, truncated to their last 5 places
        :param award_id:
        :param column:
        :return:
        """
        raw = self[column]
        vals = map (lambda x:x.strip(), raw.split(','))
        return list (set (vals))

    def get_dup_award_ids (self, column):
        tally = {}
        dups = []
        raw = self[column]
        vals = map (lambda x:x.strip(), raw.split(','))
        for val in vals:
            if val in tally:
                tally[val] = tally[val] + 1
                dups.append(val)
            else:
                tally[val] = 1
        return list(set(dups))


# class AwardIdDatasetReader(CsvReader):
class AwardIdDatasetReader(FilteringCsvReader):

    """
    CVS reader that provides:
    - doi lookup
    - pid lookup

    Filtering of records (e.g.,  {'start':'2020-01-01', 'end':'2020-02-01'})
    Sorting of records (e.g., {'field':'pid'})

    Note: Dates are in YYYY-MM-DD format

    """
    record_class = AwardIdDatasetRecord
    award_id_column = None # specified by subclass

    # def __init__ (self, path):
    def __init__ (self, path, filter_args={}, sort_args={}):
        self.path = path
        self.name = os.path.basename(self.path)

        # CsvReader.__init__ (self, path)
        FilteringCsvReader.__init__ (self, path, filter_args, sort_args)

        self.pid_map = {}
        self.doi_map = {}

        self.pid_buckets = ListBucketDict()
        self.doi_buckets = ListBucketDict()

        self.dup_pids = {} # the buckets contain dois
        self.dup_dois = {} # the buckets contain pids

        for rec in self.data:
            pid = rec['pid']
            doi = rec['doi']
            
            self.pid_buckets.add(pid, rec)
            self.doi_buckets.add(doi, rec)
 
        for pid in self.pid_buckets.keys():
            bucket = self.pid_buckets[pid]
            self.pid_map[pid] = bucket[0]
            if len(bucket) > 1:
                self.dup_pids[pid] = map (lambda x:x['doi'], bucket)
        
        for doi in self.doi_buckets.keys():
            bucket = self.doi_buckets[doi]
            self.doi_map[doi] = bucket[0]
            if len(bucket) > 1:
                self.dup_dois[doi] = map (lambda x:x['pid'], bucket)

    def get_record (self, pid):
        return self.pid_map[pid]

    def get_record_for_doi (self, doi):
        return self.doi_map[doi]

    def get_recs_having_award_id(self):
        # return filter (lambda x:len(x['kuali_verified_award_ids'].strip()) > 0 , self.data)
        return filter (lambda x:len(x[self.award_id_column].strip()) > 0 , self.data)

    def get_unique_award_ids (self, award_id_column=None):
        if award_id_column is None:
            award_id_column = self.award_id_column
        recs_with_award_id = self.get_recs_having_award_id()
        award_ids = []
        for rec in recs_with_award_id:
            ids = rec[award_id_column].split(',')
            award_ids += ids
        return list(set(award_ids))

    def get_total_award_ids (self):
        recs_with_award_id = self.get_recs_having_award_id()
        award_id_cnt = 0
        for rec in recs_with_award_id:
            ids = rec[self.award_id_column].split(',')
            award_id_cnt += len(ids)
        return award_id_cnt

    def cache_coverage_report (self, award_id_column=None):
        cache = KualiCache()
        if award_id_column is None:
            award_id_column = self.award_id_column
        print 'award_id_column:', award_id_column
        missing_award_ids = []
        for award_id in self.get_unique_award_ids(award_id_column):
            if not cache.find_kuali_id (award_id):
                # print 'not found: ', award_id
                missing_award_ids.append(award_id)
        missing_award_ids.sort()
        print '{} missing award_ids from cache'.format(len(missing_award_ids))
        for award_id in missing_award_ids:
            print '-', award_id

    def dup_award_ids_report (self, award_id_column=None):
        if award_id_column is None:
            award_id_column = self.award_id_column
        print 'DUP award ids report'
        for rec in self.get_recs_having_award_id():
            dups = rec.get_dup_award_ids(award_id_column)
            if len(dups) > 0:
                print '- {} - {}'.format(rec['pid'], dups)

if __name__ == '__main__':
    comp_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_id_data-Composite.csv'
    partial_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL.csv'
    doi_ref_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv'

    my_filter_args = {'start':'2020-01-01', 'end':'2020-02-01'}
    my_sort_args = {'field':'pid'}

    reader = AwardIdDatasetReader(partial_path)
    print 'reader has {}'.format(len(reader.data))



    if 0:
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


