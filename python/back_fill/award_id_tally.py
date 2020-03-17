"""
AwardIdReporter - consumes a PID Feed.

- tally is a mapping from pid to list of award_is for that pid

- tally can be written to disk as json
"""

__author__ = 'ostwald'

import os, sys, re, time, traceback, codecs, json
from UserDict import UserDict
sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin import CONFIG
from ncarlibadmin.model import FedoraObject, FedoraValidationError
from ncarlibadmin.batch import feed as feeds, PIDReporter
from notes_mods import NotesMODS
import lxml.etree as ET

OLD_FUNDER_PAT = re.compile('.*?:[\s]+([\S]*)')  #  abbrev ignored


"""
the pid processing method ....
- the aim is reporing over the PIDs in the feed
"""

class AwardIdReporter (PIDReporter):

	batch_size = 500
	max_to_process = 2000
	delay_secs = 0

	def __init__(self, feed):
		PIDReporter.__init__(self, feed)
		self.tally = {}

	def process(self):

		PIDReporter.process(self)
		print '  ... done processing'

	def processPid (self, pid):
		# print 'processPid', pid
		try:
			fedoraObj = FedoraObject (pid)
			mods_xml =  fedoraObj.get__MODS_stream()

			mods = NotesMODS (mods_xml, pid)

			funding_notes = mods.get_funding_notes()
			award_ids = map (lambda x:x.text, funding_notes)

			self.tally[pid] = award_ids

			self.processed = self.processed + 1
			if self.processed % 100 == 0:
				# print pid, ' processed'
				print '%d/%d' % (self.processed, self.numResults)
				time.sleep(self.delay_secs)
		except:
			# traceback.print_exc()
			raise Exception, 'could not ProcessItem "%s": %s' % (pid, sys.exc_info()[1])

	def report (self):
		pids = self.tally.keys()
		pids.sort()
		print 'there are {} results'.format(len(self.tally.keys()))
		for pid in pids:
			print '\n', pid
			for award_id in self.tally[pid]:
				print '-',award_id


	def write_as_json (self, dest="AWARD_ID_TALLY.json"):

		fp = codecs.open(dest, 'w', 'utf8')
		fp.write (json.dumps(self.tally, indent=3))
		fp.close()
		print 'tally written to {}'.format(dest)


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

class AwardIdTally (UserDict):
	"""
	Reads in json file and provides mapping API from pid to award_ids

	- get_multies - returns only pids that have more than one award_id

	-- calls function that filters the data according to provided predicate
		pred = function (item)

	"""
	def __init__ (self, path=None):
		"""
		open completion, se;f.data holds the mapping read as json
		:return:
		"""
		self.data = {}
		try:
			contents = open (path, 'r').read()
			data = json.loads(contents)

			# print json.dumps(data, indent=3)

			self.data = data
		except:
			traceback.print_exc()

	def get_multies (self):
		return self.filter (lambda pid, award_ids: len(award_ids) > 1)

	def filter (self, predicate):
		filtered = {}
		for key in self.keys():
			value = self.data[key]
			# print 'key: {},  value: {}'.format(key, value)
			if predicate(key, value):
				filtered [key] = value
		return filtered

	def report (self, pid_map=None):
		if pid_map is None:
			pid_map = self.data
		pids = pid_map.keys()
		pids.sort()
		for pid in pids:
			print '\n', pid
			for id in pid_map[pid]:
				print ' - ',id

def main (feed):
	reporter = AwardIdReporter(feed)
	reporter.process()
	reporter.report()
	reporter.write_as_json()

def get_dup_pred (pid, award_ids):
	normalize_pat = re.compile('[^a-zA-Z0-9]')
	normalized_ids = map (lambda x: normalize_pat.sub ('', x), award_ids)

	soup = ''.join(normalized_ids)
	for id in normalized_ids:
		cnt = soup.split (id)
		if len(cnt) > 2:
			return True

if __name__ == '__main__':

	print 50*'-'
	print ' fedora server:', CONFIG.get("fedora", "SERVER")

	if 0:   # reporter
		feed = getFeed()
		print '%d items in feed' % feed.size()
		main(feed)

	if 1:
		path = '/Users/ostwald/devel/opensky/pubs_to_grants/python/back_fill/AWARD_ID_TALLY_1292.json'
		tally = AwardIdTally(path=path)
		multies = tally.get_multies()

		duppers = tally.filter (get_dup_pred)

		print 'tally has {} keys'.format(len(tally.keys()))
		print 'multies has {} keys'.format(len(multies.keys()))
		print 'duppers has {} keys'.format(len(duppers.keys()))

		tally.report (duppers)
		
		if 1:
			outpath = "/Users/ostwald/tmp/dupper.json"
			fp = open (outpath, 'w')
			fp.write (json.dumps (duppers, indent=3))
			print 'duppers written to {}'.format(outpath)

	if 0:

		pat = re.compile ('[ _\-\:]')

		pat = re.compile('[^a-zA-Z0-9]')
		print pat.sub ('', sample)

		sample = "asdf asdf :asd{}+&fA4asdf   _end"

		# m = pat.search (sample)
		# if m:
		# 	print 'MATCH'
		# else:
		# 	print 'NOPE'

