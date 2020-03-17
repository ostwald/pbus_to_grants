import os, sys, re

sys.path.append ('/Users/ostwald/devel/opensky/pubs_to_grants/python')
from csv_processor import get_unique_values

from kuali_client import KualiClient



#
# class KualiResultTally:
#
#     def __init__ (self, csv_path):
#         self.tally = None
#         self.kuali = KualiClient ()
#         self.award_ids = get_unique_values(csv_path, 'kuali_verified_award_ids')
#         print '{} award ids found'.format(len (self.award_ids))
#
#     def get_kuali_hits (self, award_id):
#         return self.kuali.get_num_hits(award_id)
#
#     def process (self):
#         self.tally = {}
#         for id in self.award_ids:
#             num_hits = self.get_kuali_hits(id)
#             self.tally[id] = num_hits
#             # print ' - {} ({})'.format(id, num_hits)
#
#         keys = self.tally.keys()
#         keys.sort(key=lambda x:-self.tally[x])
#
#         for key in keys:
#             print '- {} ({})'.format(key, self.tally[key])
#
#
# if __name__ == '__main__':
#     path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
#     tally = KualiResultTally(path)
#     tally.process()



