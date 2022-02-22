"""
Encapsulates the DOI Reference table, which holds the pid, doi, creation, and lastmod fields
for each record in OpenSky that is associated with a DOI.

The table source is made by "solr_fetcher" which queries opensky and writes results
as a delimited file.

Reads the data as CSV file
-  pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv

note: The table data file is made by "solr_fetcher" which queries opensky and writes results
as a delimited file.
"""

import os, sys, json
from kuali_cache import KualiCache
from csv_reader import CsvRecord, CsvReader
from award_id_dataset_csv_reader import AwardIdDatasetReader, AwardIdDatasetRecord

from ncarlibadmin.solr.solr import pidExists

def filename2pid (s):
    return ':'.join(s.split('.')[0].split('_'))

def pid2filename(s):
    return s.replace(':', '_') + '.xml'

class DOIRefRecord(AwardIdDatasetRecord):
    def __init__ (self, data, schema):
        AwardIdDatasetRecord.__init__(self, data, schema)

    def get_award_ids(self):
        return AwardIdDatasetRecord.get_award_ids(self, 'award_ids')

    # self.award_id_list = filter (None, map (lambda x:x.strip(), self['award_ids'].split(',')))



class DOIRefReader(AwardIdDatasetReader):

    record_class = DOIRefRecord
    award_id_column = 'award_ids'

    def __init__ (self, path=None):
        if path is None:
            path = "/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv"
        self.last_mod_map = {}
        AwardIdDatasetReader.__init__ (self, path)

        for rec in self.data:
            self.last_mod_map[rec['lastmod']] = rec


    def report_missing_cache_files (self):
        """
        NOTE: the csv is assumed to be DOI-REFERENCE_TABLE
        do the pids in the OpenSky Index match up with cached pids?
        :return:
        """
        cached_xml_dir = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/metadata'
        opensky_pids = self.pid_map.keys()
        opensky_pids.sort()
        for service in ["crossref", "wos"]:
            print ("\nMissing in " + service)
            filenames = sorted(os.listdir (os.path.join (cached_xml_dir, service)))
            for pid in opensky_pids:
                filename = pid2filename(pid)

                if not os.path.exists(os.path.join (cached_xml_dir, service, filename)):
                    print pid

    def compare_cached_xml_to_reference_pids(self):
        """
        NOTE: the csv is assumed to be DOI-REFERENCE_TABLE
        do the pids cached match up with the pids in the OpenSky Index?
        :return:
        """
        cached_xml_dir = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/metadata'
        index_pids = self.pid_map.keys()
        # print ('\nobsolete cache files')
        extra_report = {}
        for service in ["crossref", "wos"]:
            extra_cached_pids = []
            # print ('\n' + service + '----------------------')
            xml_dir = os.path.join (cached_xml_dir, service)
            filenames = filter (lambda x: x[0] != '.', os.listdir(xml_dir))
            filenames.sort()
            for filename in filenames:
                pid = filename2pid(filename)
                if not pid in index_pids:
                    extra_cached_pids.append(pid)
                    # print ' {}\t{}'.format(pid, os.path.join (xml_dir, filename))
            extra_report[service] = extra_cached_pids
        return extra_report

    def report_extra_cached_metadata(self, pids=None):
        if pids is None:
            data = self.compare_cached_xml_to_reference_pids()
            pids = data['wos']
        for pid in pids:
            exists = pidExists(pid)

            # print 'exists:', exists
            print '{}\t{}'.format(pid, exists)

    def report_legacy_award_ids(self):
        """
        Note: there are likely to be more records with legacy award_ids that
        are not in the DOI_REFERENCE spreadsheet! E.g., as of 11/22/21 there are
        416 records from BEFORE 2014 that have legacy award_ids.

        :return:
        """
        cnt = 0
        for rec in self.data:
            if rec['legacy_award_ids']:
                print rec['pid'], rec['legacy_award_ids']
                cnt += 1

        print cnt, 'recs with legacy award Ids'

    def report_skip_award_ids(self):
        """
        Note: there are likely to be more records with legacy award_ids that
        are not in the DOI_REFERENCE spreadsheet! E.g., as of 11/22/21 there are
        416 records from BEFORE 2014 that have legacy award_ids.

        :return:
        """
        skip_award_ids = [  # see https://stage.ucar.dgicloud.com/admin/config/system/openskydora
            '999999',
            'DEAC0576L01830',
            'DEAC0576RL01830',
            'DEAC5207NA27344',
            'DEAC0500OR22725',
            'DEAC3608GO28308',
        ]
        cnt = 0
        for rec in self.data:
            award_ids = filter (None, rec.get_award_ids())
            if len(award_ids) > 0:
                # print '\n' + rec['pid']
                for award_id in award_ids:
                    # print ' - ', award_id
                    if award_id in skip_award_ids:
                        print '- {} - {}'.format(rec['pid'], award_id)
                        cnt += 1

        print cnt, 'skip award_ids found'

    def report_duplicate_award_ids_per_record(self):
        """
        find records in which there are duplicate award_ids
        :return:
        """
        print "Looking for dup award_ids ..."
        for rec in self.data:

            pid = rec['pid']
            # ids = rec.award_id_list
            ids = rec.get_award_ids()
            # tally = make_id_tally(ids)
            dups = make_dup_tally(ids)
            for id in dups.keys():
                if dups[id] > 1:
                    print '{} - {} dups  ({})'.format(pid, id, dups[id])

    def get_non_kuali_award_ids(self):
        """
        Report award_ids that are not represented in cache
        :return:
        """
        cache = KualiCache()
        bad_award_ids = {} # map award_id to pids in which it appears
        for rec in self.data:

            pid = rec['pid']
            ids = rec.get_award_ids()
            for id in ids:
                # kuali_id = cache.find_kuali_id(id)
                # if not kuali_id:
                #     print '- {} - {}'.format(pid, id)
                #     kuali_id = cache.find_kuali_id(id)
                if not id in cache.values():
                    # print '- {} - {}'.format(pid, id)
                    pids = bad_award_ids.has_key(id) and bad_award_ids[id] or []
                    pids.append(pid)
                    bad_award_ids[id] = pids
        return bad_award_ids

def make_id_tally (ids):
    """
    utility - return dict of award_id to number of occurrences
    :param ids: list af award_ids
    :return:
    """
    tally = {}
    for id in ids:
        hits = tally.has_key(id) and tally[id] or 0
        hits = hits + 1
        tally[id] = hits
    return tally

def make_dup_tally(ids):
    """
    utility - return dict of award_id to number of occurrences for those award_ids that
    have 2 or occurrences
    :param ids:
    :return:
    """
    tally = make_id_tally(ids)
    for key in tally.keys():
        if tally[key] > 2:
            del tally[key]
    return tally



if __name__ == '__main__':
    # path= '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-LEGACY-REFERENCE_TABLE.csv'
    path= '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    # path= '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/ALL-FUNDING-REFERENCE_TABLE.csv'
    reader = DOIRefReader(path)
    print '{} records'.format(len(reader.data))
    cache = KualiCache()
    # reader.cache_coverage_report()
    # reader.report_legacy_award_ids()
    reader.report_duplicate_award_ids_per_record()
    reader.report_skip_award_ids()


    if 0: # verify that ids in DOI Ref are known to cache
        bad_award_ids = reader.get_non_kuali_award_ids()
        ids = filter(None, bad_award_ids.keys())
        ids.sort()
        print 'bad_award_ids ({}_ - {}'.format(len(ids), ids)
        for id in ids:
            # print '- {} ({})'.format(id, len(bad_award_ids[id]))
            # print '{}\t{}'.format(id, '\t'.join(bad_award_ids[id])) #~/tmp/bog_award_ids.tsv
            print '{}\t{}'.format(id, cache.find_kuali_id(id)) #~/tmp/

    if 0:
        rec = reader.pid_map['articles:23270']
        ids = rec.get_award_ids()
        for id in ids:
            print id
        tally = make_dup_tally(ids)
        print json.dumps(tally, indent=2)

    if 0:
        pids = [
            'articles:22870',
            'articles:22902',
            'articles:23005',
            'articles:23007',
            'articles:23009',
            '',
        ]
        reader.report_extra_cached_metadata(pids)