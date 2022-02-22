"""
similar to smart_partial_txt, create a award tally by column so it can be
compared against smart_partial
"""
import os, sys, re, traceback
from smart_partial import SmartPartialRecord, SmartPartialReader

class DoiRefRecord (SmartPartialRecord):
    pass

class DoiRefReader (SmartPartialReader):
    def get_award_id_columns (self):
        return self.header[-1:]

if __name__ == '__main__':
    path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    reader = DoiRefReader (path)

    print 'read',len(reader.data)

    print reader.report_tally_map()
    reader.write_tally_map()