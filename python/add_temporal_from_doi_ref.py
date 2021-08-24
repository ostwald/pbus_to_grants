"""
Add the temporal data from DOI Reference Table to the award_data table
and write to new table.
"""

import os, sys, json
# sys.path.append('/Users/ostwald/devel/projects/library-admin')
# from ncarlibadmin import CONFIG

from doi_reference import  DOIRefReader
from award_id_dataset_csv_reader import AwardIdDatasetReader

class TableMerger:
    
    def __init__(self, award_data, doi_ref):
        self.award_data = award_data
        self.doi_ref = doi_ref

    def make_new_rec_data(self, pid):
        award_rec = self.award_data.pid_map[pid]
        new_rec_data = list(award_rec.data)

        try:
            ref_rec = self.doi_ref.pid_map[pid]
            new_rec_data.append(ref_rec['lastmod'])
            new_rec_data.append(ref_rec['created'])
        except KeyError, pid:
            print 'WARN: pid ({}) not found in doi_ref'.format(pid)

        return new_rec_data

    def get_header (self):
        header = list(self.award_data.header)
        header.append ('lastmod')
        header.append ('created')
        return header

    def get_merged_records (self):
        records = []
        for pid in self.award_data.pid_map.keys():
            new_rec_data = self.make_new_rec_data(pid)
            records.append (new_rec_data)
        return records


    def write_merged_data(self, out_path='/Users/ostwald/tmp/MERGED_AWARD_DATA.tsv'):
        records = []
        records.append (self.get_header())
        data_records = self.get_merged_records()

        records = records + data_records
        content = '\n'.join(map (lambda x:'\t'.join(x), records))

        fp = open(out_path, 'w')
        fp.write (content)
        fp.close()
        print 'wrote {} records to {}'.format(len(data_records), out_path)


if __name__ == '__main__':
    award_data_path= '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Cached_Award_Data.csv'
    award_data = AwardIdDatasetReader (award_data_path)
    doi_ref_data_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    doi_ref = DOIRefReader(doi_ref_data_path)
    merger = TableMerger (award_data, doi_ref)

    merger.write_merged_data()

    # print merger.

