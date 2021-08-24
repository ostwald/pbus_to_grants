"""
The SMART_PARTIAL.txt file was created by pubs_to_grants/php/doi_tester.php

We add to this table each time we run doi_tester, so some of the rows were made long ago
and some were just recently made.

Here are the columns:
pid | doi | pub_date | wos_award_ids | crossref_award_ids | validated_award_ids

First of all, we want to know if the "skipped award_ids" show up in the various columns

Second, we want to get an idea of the ids that are in the different columns and their frequency
and their reliability.

See the output from report_tally_map

"""

import os, sys, re
from csv_processor import CsvRecord, CsvReader
from UserDict import UserDict

def normalize_id(raw):
    # return raw[-5:]
    return raw

class TallyDict (UserDict):
    """
    data is of form
    {
        key : [ value1, value2]
    }
    We want to see which key has most values, etc
    """
    def __getitem__ (self, key):
        """
        return empty list if the key does not yet exist
        :param key:
        :return:
        """
        if not self.data.has_key(key):
            return []
        else:
            return self.data[key]

    def sorted_keys(self):
        """
        sort keys by length of values for each bucket
        :return:
        """
        keys = self.data.keys()
        keys.sort(key=lambda x:-len(self[x]))
        return keys


class SmartPartialRecord (CsvRecord):

    def get_award_ids (self, column):
        """
        returns a list of award_ids, truncated to their last 5 places
        :param award_id:
        :param column:
        :return:
        """
        raw = self[column]
        vals = map (lambda x:x.strip(), raw.split(','))
        # truncated = filter (None, map (lambda x: len(x)>5 and x[-5:] or None, vals))
        truncated = filter (None, map (lambda x: len(x)>5 and normalize_id(x) or None, vals))
        # we only want the unique values (e.g. crossref lists dups sometimes)
        return list (set (truncated))

class SmartPartialReader (CsvReader):
    record_class = SmartPartialRecord

    def __init__ (self, path):
        self.path = path
        CsvReader.__init__(self, path)
        self._tally_map = None
        self._pid_map = None

    def get_record (self, pid):
        if self._pid_map is None:
            self._pid_map = {}
            for rec in self.data:
                self._pid_map[rec['pid']] = rec
        return self._pid_map[pid]

    def get_award_id_columns (self):
        return self.header[-3:]

    def tally_awards_in_column(self, column):
        """
        tally the pids in which an award_id appears (in specified column)
        :param column:
        :return:
        """
        tally = TallyDict()
        for rec in self:
            ids = rec.get_award_ids (column)
            for id in ids:
                vals = tally[id]
                vals.append(rec['pid'])
                tally[id] = vals
        return tally
    
    def get_tally_map (self):
        if self._tally_map is None:
            self._tally_map = {}
            # for field in self.header[-3:]:
            for field in self.get_award_id_columns():
                self._tally_map[field] = self.tally_awards_in_column(field)
        return self._tally_map

    def report_tally_map (self):
        tally_map = self.get_tally_map()
        # kuali_tally = tally_map['validated_award_ids']
        kuali_tally = tally_map[self.header[-1]]

        lines = []
        # header = ['award_id'] + self.header[-3:]
        header = ['award_id'] + self.get_award_id_columns()
        lines.append (header)
        # for award_id in sorted_keys:
        for award_id in kuali_tally.sorted_keys():
            line = [award_id]
            for field in self.get_award_id_columns():
                # print 'award_id:', award_id, '  field:', field
                line.append (len(tally_map[field][award_id]))
            lines.append (line)

        if 0:
            for line in lines:
                print line

        return lines

    def write_tally_map(self):
        report_dir = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/reports'
        filename = os.path.splitext(os.path.basename(self.path))[0]
        outpath = os.path.join(report_dir, filename + '-TALLY.tsv')
        fp = open(outpath, 'w')
        content = '\n'.join(map (lambda x:'\t'.join(x), map (lambda x:map (str, x), self.report_tally_map())))
        fp.write(content)
        fp.close()
        print 'wrote to', outpath


    def report_award_id (self, award_id):
        tally_map = self.get_tally_map()
        normalized_id = normalize_id(award_id)

        # for column in self.header[-3:]:
        for column in self.get_award_id_columns():
            tally = tally_map[column]
            print '\n{} ({})'.format(column, len (tally[normalized_id]))
            if 0:  # print all the pids and their award_ids
                for pid in tally[normalized_id]:
                    rec = self.get_record(pid)
                    ids = rec.get_award_ids(column)
                    print '- {}: {}'.format(pid, ids)




if __name__ == '__main__':
    path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL_OLD.csv'
    # path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Cached_Award_Data.csv'
    reader = SmartPartialReader (path)

    print 'read',len(reader.data)

    # reader.report_tally_map()
    reader.write_tally_map()

    if 0: # report on a given award_id
        award_id = '1852977'
        reader.report_award_id('1852977')
