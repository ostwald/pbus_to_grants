import sys, os, csv, codecs
from UserList import UserList


"""
read a Kuali DOI Testing spreadsheet and print out the unique award ids
"""

class CsvRecord:

    def __init__ (self, data, schema):
        self.data = data
        self.schema = schema


    def __getitem__(self, fieldname):
        index = self.schema.index (fieldname)
        return self.data[index]

class CsvReader(UserList):

    record_class = CsvRecord

    def __init__ (self, path):

        self.header = None
        rawdata = []

        # with open(path, 'rb') as csvfile:
        with codecs.open(path, 'rb') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for i,row in enumerate(csv_reader):
                if i == 0:
                    self.header = row
                else:
                    rawdata.append(row)

        self.data = map (lambda x:self.record_class (x, self.header), rawdata)
        print '{} data records'.format(len(self.data))

def get_unique_values (path, field):
    csv = CsvReader(path)
    all_ids = []
    for record in csv:
        ids = filter (None, map (lambda x:x.strip(), record[field].split(',')))
        if ids:
            all_ids += ids
    print '\n{}'.format(os.path.basename(path))
    print 'all_ids has %d items' % len (all_ids)
    unique_vals = set(all_ids)
    print 'unique_vals has %d items' % len (unique_vals)
    unique_vals = list(unique_vals)
    unique_vals.sort()
    return unique_vals

def show_unique_values (path, field='kuali_verified_award_ids'):

    unique_vals = get_unique_values(path, field)
    unique_vals.sort()
    if 0:  # show items
        for id in unique_vals:
            print id




if __name__ == '__main__':

    # path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/cvs/Award_id_data.csv'
    path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/cvs/Sandbox_Test.csv'
    show_unique_values(path, 'validated_award_ids')

    # show_award_id_tally (path)
    if 0:
        paths = [
            '/Users/ostwald/tmp/DOI_KUALI_TESTING_Naive_partial.csv',
            '/Users/ostwald/tmp/DOI_KUALI_TESTING_SMART_partial.csv',
            '/Users/ostwald/tmp/DOI_KUALI_TESTING_STRICT.csv',
        ]

        for path in paths:
            show_stats(path)
