"""
Consumes a CSV file (e.g.,  SMART_PARTIAL.csv) into

Records that are field-addressable - object['fieldname']

"""

import os, sys, time, codecs

import csv
from UserList import UserList

class CsvRecord:
    """
    field-addressable - object['fieldname']
    """
    def __init__ (self, data, schema):
        self.data = data
        self.schema = schema

    def __getitem__(self, fieldname):
        index = self.schema.index (fieldname)
        return self.data[index]

def sanitize (path):
    UGLY_PAT = unichr(8218) + unichr(196) + unichr(234)

    fp = open (path, 'r')
    raw = fp.read()
    content = unicode (raw, 'utf8')
    fp.close()
    content = content.replace (UGLY_PAT, '-')
    content = content.encode('ascii', errors='ignore')
    fp = open (path, 'w')
    fp.write (content)
    fp.close()
    # print 'sanitized {}'.format(path)

class CsvReader(UserList):

    record_class = CsvRecord

    def __init__ (self, path):
        content = sanitize(path)

        self.header = None
        rawdata = []
        encoding = 'ISO-8859-1'
        # encoding = 'utf-8'


        with open(path, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for i,row in enumerate(csv_reader):
                if i == 0:
                    self.header = row
                else:
                    if len(row) > 0:
                        rawdata.append (row)

        self.data = map (lambda x:self.record_class (x, self.header), rawdata)
        # print '{} data records'.format(len(self.data))

    def report (self):
        for rec in self.data:
            if len(rec['kuali_verified_award_ids'].strip()) > 0:
                print ' - {} {}'.format(rec['pid'], rec['kuali_verified_award_ids'])

def compare (path1, path2):
    reader1 = CsvReader (path1)
    reader2 = CsvReader (path2)
    dups=[]
    for key in reader1.pid_map.keys():
        if key in reader2.pid_map.keys():
            dups.append (key)

    print 'dups {}'.format(len(dups))

    print 'NON DUPS'
    for pid in reader1.pid_map.keys():
        if not pid in dups:
            print '- ',pid

    # for dup in dups:
    #     print ' -',dup



if __name__ == '__main__':


    path1 = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/cvs/Award_id_data.csv'
    path2 = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/cvs/Sandbox_Test.csv'

    # reader = CsvReader(path2)
    # print '{} records read'.format(len(reader.data))

    compare (path1, path2)



