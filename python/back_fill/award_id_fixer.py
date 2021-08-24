"""
AwardIdFixer - consumes a PID Feed of records with any award_id and
- removes dups
- normalized award_ids

"""

__author__ = 'ostwald'

import os, sys, re, time, traceback, codecs, json
from UserDict import UserDict
sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin import CONFIG
from ncarlibadmin.model import FedoraObject, FedoraValidationError
from ncarlibadmin.batch import feed as feeds, PIDProcessor
from notes_mods import NotesMODS
import lxml.etree as ET

# OLD_FUNDER_PAT = re.compile('.*?:[\s]+([\S]*)')  #  abbrev ignored


"""
the pid processing method ....
- the aim is reporing over the PIDs in the feed
"""

class MyProcessor (PIDProcessor):
	def processBatch(self, batch):
		"""
		batch is a list of pids
		"""
		# print "\n%d records in batch" % len(batch)
		for pid in batch:
			try:
				self.processPid(pid)
			except Exception, msg:
				print "trouble processing record!: %s" % msg
				traceback.print_exc()
				sys.exit()

class AwardIdFixer (MyProcessor):

	batch_size = 500
	max_to_process = 1300
	delay_secs = .5
	dowrites = 1

	def __init__(self, feed):
		PIDProcessor.__init__(self, feed)
		NotesMODS.dowrites = self.dowrites
		self.processed = 0

	def process(self):

		PIDProcessor.process(self)
		print '  ... done processing'

	def processPid (self, pid):

		# if cmp(pid, 'articles:17025') < 0:
		if cmp(pid, 'articles:22578') < 0:
			print 'skipping {}'.format(pid)
			self.processed = self.processed + 1
			return

		# print 'processPid', pid
		try:
			fedoraObj = FedoraObject (pid)
			mods_xml =  fedoraObj.get__MODS_stream()

			mods = NotesMODS (mods_xml, pid)
			mods.do_back_fill()

			self.processed = self.processed + 1
			if 1 or self.processed % 100 == 0:
				# print pid, ' processed'
				print '%d/%d' % (self.processed, self.numResults)
			time.sleep(self.delay_secs)
		except:
			# traceback.print_exc()
			raise Exception, 'could not ProcessItem "%s": %s' % (pid, sys.exc_info()[1])

def getFeed():
	args = {
		'params' :
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


def main (feed):
	fixer = AwardIdFixer(feed)
	fixer.process()


if __name__ == '__main__':

	print 50*'-'
	print ' fedora server:', CONFIG.get("fedora", "SERVER")

	if 1:   # fixer
		feed = getFeed()
		print '%d items in feed' % feed.size()
		main(feed)
