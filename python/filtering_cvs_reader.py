"""
filter records according to a filter spec

"""
import sys, time, urllib, codecs, json, copy
# sys.path.append('/Users/ostwald/devel/python-lib')
from csv_reader import CsvRecord, CsvReader


class SortSpec:
    """
    start and end are in 2005-03-03' format
    """
    default_spec = {
        'field' : 'pub_date',
        'reverse' : False,
    }

    def __init__ (self, **args):
        spec = self.default_spec
        spec.update(args)
        self.spec = spec

class FilterSpec:
    """
    start and end are in 2005-03-03' format
    """
    default_spec = {
        'start' : '2014-01-01',
        'end' : '2020-12-31',
        'date_field' : 'pub_date',
    }

    def __init__ (self, **args):
        spec = copy.copy(self.default_spec)
        spec.update(args)
        self.spec = spec

    def accept (self, rec):

        date_field = self.spec['date_field']
        if rec[date_field] < self.spec['start']:
            return False
        if rec[date_field] > self.spec['end']:
            return False
        return True

class FilteringCsvReader (CsvReader):

    def __init__ (self, path, filter_args={}, sort_args={}):
        self.sort_spec = SortSpec(**sort_args)
        self.filter_spec = FilterSpec(**filter_args)
        CsvReader.__init__ (self, path)
        print '{} records before filtering'.format(len (self.data))
        # print 'filter spec: {}'.format(self.filter_spec.spec)
        if filter_args is not None:
            self.filter_data()

        if self.sort_spec is not None:
            self.data.sort (key=lambda x:x[self.sort_spec.spec['field']])
            if self.sort_spec.spec['reverse']:
                self.data.reverse()

    def filter_data(self):
        # filtered = []
        # for rec in self.data:
        #     if self.filter_spec.accept(rec)
        filtered = filter (self.filter_spec.accept, self.data)
        self.data = filtered

if __name__ == '__main__':
    filter_args = {'start':'2020-01-01', 'end':'2020-02-01'}
    sort_args = {'field':'pid'}
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    reader = FilteringCsvReader (csv_path, filter_args, sort_args)
    print '{} records after filtering'.format(len(reader.data))

    for rec in reader.data:
        print '{} - {}'.format(rec['pid'], rec['pub_date'])
