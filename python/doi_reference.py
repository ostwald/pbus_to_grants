"""
Encapsulates the DOI Reference table, which holds the pid, doi, creation, and lastmod fields
for each record in OpenSky that is associated with a DOI.

The table source is made by "solr_fetcher" which queries opensky and writes results
as a delimited file.

Reads the data as CSV file
-  pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv

note: The table data file is made by "solr_fetcher" which queries opensky and writes results
as a delimited file.
"""

import os, sys, json
from csv_reader import CsvRecord, CsvReader

# sys.path.append('/Users/ostwald/devel/projects/library-admin')
# from ncarlibadmin import CONFIG

class DOIRefRecord(CsvRecord):

    def __init__ (self, data, schema):
        CsvRecord.__init__(self, data, schema)

class DOIRefReader(CsvReader):

    record_class = DOIRefRecord

    def __init__ (self, path=None):
        if path is None:
            path = "/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv"
        self.last_mod_map = {}
        self.pid_map = {}
        CsvReader.__init__ (self, path)

        for rec in self.data:
            self.last_mod_map[rec['lastmod']] = rec
            self.pid_map[rec['pid']] = rec



if __name__ == '__main__':
    reader = DOIRefReader()
    print '{} records'.format(len(reader.data))

    cnt = 0
    for rec in reader.data:
        if rec['legacy_award_ids']:
            print rec['pid'], rec['legacy_award_ids']
            cnt += 1
    print cnt, 'recs with legacy award Ids'