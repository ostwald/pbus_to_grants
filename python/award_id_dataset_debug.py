"""
Trying to get to the bottom of the dup dois in DOI Reference
"""
import os, sys, json
from award_id_dataset_csv_reader import AwardIdDatasetReader

# sys.path.append('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin import CONFIG
from ncarlibadmin.batch import feed as feeds

COMP_PATH = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_id_data-Composite.csv'
PARTIAL_PATH = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL_v2.csv'
DOI_REF_PATH = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv'

class AwardDatasetDebugger (AwardIdDatasetReader):

    def __init__ (self, path):
        AwardIdDatasetReader.__init__(self, path)
        # self.report_dups()


    def report_dups (self):
        if len(self.dup_pids) > 0:
            print '{} dup pids found'.format(len(self.dup_pids))
            for pid in self.dup_pids.keys():
                print '\n{}'.format(pid)
                for doi in self.dup_pids[pid]:
                    print '-', doi

        if len(self.dup_dois) > 0:
            print '{} dup dois found'.format(len(self.dup_dois))
            for i, doi in enumerate(self.dup_dois.keys()):
                print '\n{}/{} - {}'.format(i, len(self.dup_dois), doi)
                for pid in self.dup_dois[doi]:
                    print self.pid_map[pid]

    def dups_to_tabdelimited (self, delimiter=','):
        lines = []
        lines.append (self.header)
        for doi in self.dup_dois.keys():
            for i, pid in enumerate(self.dup_dois[doi]):
                line = self.pid_map[pid].data
                if i < 0:  # only show doi once
                    line[0] = ''
                lines.append (line)
        return '\n'.join (map (lambda x:delimiter.join(x), lines))

    def write_dup_tabdelimited(self, out_path='/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DUP_DOI_REPORT.csv'):
        fp = open(out_path, 'w')
        fp.write(self.dups_to_tabdelimited(','))
        fp.close()
        print 'wrote to ', out_path



if __name__ == '__main__':
    reader = AwardDatasetDebugger(COMP_PATH)
    # reader.report_dups()
    # print reader.dups_to_tabdelimited()
    # reader.write_dup_tabdelimited()