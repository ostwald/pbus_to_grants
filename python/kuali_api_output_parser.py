import os, sys,re

"""
We are parsing a static report to get data for a html-based tally for
number of Kuali API hits returned for each award_id
"""

path = '/Users/ostwald/tmp/award_ids.txt'

lines = open(path, 'r').read().split('\n')

print '{} lines'.format(len(lines))

class KRecord:

    line_pat = re.compile ('- ([\S]+) \(([0-9]+)\)(.*)')

    def __init__(self, line):
        self.line = line
        self.award_id = None
        self.hits = None
        self.notes = None
        m = self.line_pat.match(self.line)
        if m:
            print 'MATCH : {}'.format(m.group(2))
            self.award_id = m.group(1)
            self.hits = int(m.group(2))
            if len(m.group(3)) > 0:
                self.notes = m.group(3)[len(' - '):]

        else:
            print 'nope'


    def __repr__ (self):
        s = self.award_id
        s += '\n\tsize: {}'.format(self.hits)
        if self.notes is not None:
            s += '\n\tnotes: {}'.format(self.notes)
        return s


if __name__ == '__main__':
    line = '- 1755088 (17) - Management and Operation of the National Center for Atmospheric Research, 2018-2023, and Supporting Activities'
    rec = KRecord(line)

    print rec