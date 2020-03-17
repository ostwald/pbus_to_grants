"""
AwardIdReporter - consumes a PID Feed.

- tally is a mapping from pid to list of award_is for that pid

- tally can be written to disk as json
"""

__author__ = 'ostwald'

import os, sys, re, time, traceback, codecs, json
from UserDict import UserDict

sys.path.append('/Users/ostwald/devel/projects/library-utils')
sys.path.append('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin import CONFIG
from ncarlibadmin.model import FedoraObject, FedoraValidationError
from ncarlibadmin.batch import feed as feeds, PIDReporter
from notes_mods import NotesMODS, FunderNote
import lxml.etree as ET

OLD_FUNDER_PAT = re.compile('.*?:[\s]+([\S]*)')  # abbrev ignored

"""
the pid processing method ....
- the aim is reporing over the PIDs in the feed
"""


class AwardIdReporter(PIDReporter):
    batch_size = 500
    max_to_process = 2000
    delay_secs = 0

    def __init__(self, feed):
        PIDReporter.__init__(self, feed)
        self.kuali_only = []
        self.legacy_only = []
        self.both = []

    def process(self):

        PIDReporter.process(self)
        print '  ... done processing'

    def processPid(self, pid):
        # print 'processPid', pid
        try:
            fedoraObj = FedoraObject(pid)
            mods_xml = fedoraObj.get__MODS_stream()

            mods = NotesMODS(mods_xml, pid)

            # funding_notes = map(FunderNote, mods.get_funding_notes())
            funding_notes = mods.get_funding_notes()

            kuali_id_found = 0
            legacy_id_found = 0

            print '\n-', pid

            for note in funding_notes:

                award_id = note.text
                is_legacy = note.get('displayLabel') == 'Legacy funding data'

                print u'  - {}  ({})'.format(award_id, is_legacy and 'LEGACY' or 'KUALI')
                if is_legacy:
                    legacy_id_found = 1
                else:
                    kuali_id_found = 1

            if legacy_id_found and kuali_id_found:
                self.both.append(pid)
                print '  BOTH'
            elif legacy_id_found:
                self.legacy_only.append(pid)
                print '  LEGACY'

            elif kuali_id_found:
                self.kuali_only.append(pid)
                print '  KUALI'

            self.processed = self.processed + 1
            if self.processed % 100 == 0:
                # print pid, ' processed'
                print '%d/%d' % (self.processed, self.numResults)
                time.sleep(self.delay_secs)
        except:
            # traceback.print_exc()
            raise Exception, 'could not ProcessItem "%s": %s' % (pid, sys.exc_info()[1])


def getFeed():
    args = {
        'params':
            {
                'q': 'mods_note_funding_s:*'
            },
        'baseUrl': CONFIG.get("fedora", "SERVER") + CONFIG.get("fedora", "SOLR_PATH"),
    }
    feed = feeds.SolrSearchFeed(**args)

    feed.numFound = len(feed.pids)
    print 'feed: %d (%d)' % (len(feed.pids), feed.size())

    feed.pids.sort()
    # for i, pid in enumerate(feed.pids):
    # 	print '- %d - %s' % (i, pid)
    return feed


def main(feed):
    reporter = AwardIdReporter(feed)
    reporter.process()
    print 'Kuali IDs Only ({})'.format(len(reporter.kuali_only))
    print 'Legacy IDs Only ({})'.format(len(reporter.legacy_only))
    print 'Both kinds of IDs ({})'.format(len(reporter.both))


if __name__ == '__main__':

    print 50 * '-'
    print ' fedora server:', CONFIG.get("fedora", "SERVER")

    if 1:  # feed
        feed = getFeed()
        print '%d items in feed' % feed.size()

    if 1:  # reporter
        main(feed)
