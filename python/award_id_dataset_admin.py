"""
A CVS reader that compares against other tables, and against responses
from OpenSky Solr

tools for determining that pids are cashed, and for making OPENSKY_DOIS.txt, the
input to the php testDOIs service, that processes each of the DOIs and cashes the
web response, as well as any award_ids cataloged in the metadata for the OpenSky resource
 associated with that DOI.
"""

import os, sys, json
from award_id_dataset_csv_reader import CsvRecord, CsvReader

# sys.path.append('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin import CONFIG AwardIdDatasetReader
from ncarlibadmin.batch import feed as feeds

class AwardIdDatasetAdmin (AwardIdDatasetReader):

    def fetch_opensky_pids (self):
        """
        implement a solrQuery Feed to generate pids

         (doi:* AND date:[2014-01-01 TO *])
         - should fetch 5184 (VERIFIED)

        """

        query = 'mods_identifier_doi_mt:*'
        query += ' AND keyDate:[2014-01-01T00:00:00Z TO *]'
        # query += ' AND keyDate:[{} TO *]'.format(get_utc_time('2014-01-01'))

        # print 'QUERY: {}'.format(query)

        args = {
            'params' :
                {
                    # 'q': affiliation_clause + ' AND ' + date_clause,
                    # 'q': 'mods_identifier_doi_mt:*'
                    'q': query
                },
            'baseUrl': CONFIG.get("fedora", "SERVER") + CONFIG.get("fedora", "SOLR_PATH"),
        }
        feed = feeds.SolrSearchFeed(**args)
        print '{} in feed'.format(len(feed.pids))
        return feed.pids

    def get_uncached_pids(self):
        """
        """
        pids = self.pid_map.keys()
        unique_pids = list (set (pids))

        pids = self.pid_map.keys()
        pids.sort()
        print '{} pids sorted'.format(len(pids))


        print 50*'-'
        print ' fedora server:', CONFIG.get("fedora", "SERVER")
        os_pids = self.fetch_opensky_pids()
        print 'os_pids: {}'.format(len(os_pids))

        os_pids.sort()
        new_pids = []
        for pid in os_pids:
            if not pid in pids:
                new_pids.append(pid)

        print '{} new pids'.format(len(new_pids))

        outpath = '/Users/ostwald/devel/opensky/pubs_to_grants/UNCACHED-OPENSKY-PIDS.txt'
        fp = open(outpath, 'w')
        fp.write ('\n'.join(new_pids))
        fp.close()
        print 'wrote to ', outpath

    def find_uncached_pids (self, service='crossref'):
        uncached_pids = []
        pids = self.pid_map.keys()
        for pid in pids:
            filename = pid.replace (':', '_') + '.xml'
            path = os.path.join (os.path.dirname(self.path), 'metadata', service, filename)
            if not os.path.exists (path):
                # print ' - {} - {}'.format(pid, path)
                uncached_pids.append(pid)
        return uncached_pids

    def find_uncached_dois (self, service='wos'):

        uncached_dois = []
        pids = self.pid_map.keys()

        for pid in pids:
            filename = pid.replace (':', '_') + '.xml'
            path = os.path.join (os.path.dirname(self.path), 'metadata', service, filename)
            if not os.path.exists (path):
                # print ' - {} - {}'.format(pid, path)
                doi = self.pid_map[pid]['doi']
                uncached_dois.append(doi)
                print ' - {} - {}'.format(pid, doi)
        return uncached_dois

    def make_OPENSKY_DOIS (self):
        """
        This file of DOIS is input to the PHP "doi_tester", which will update the
        :return:
        """
        dois = self.find_uncached_dois()
        out_path = os.path.join (os.path.dirname(self.path), 'OPENSKY_DOIS.txt')
        fp = open(out_path, 'w')
        fp.write ('\n'.join (dois))
        fp.close()
        print 'wrote to {}'.format(out_path)

    def report_missing_paths (self, service='wos'):
        """
        use this to report the DOIs not yet cached
        :return:
        """

        uncached_pids = self.find_uncached_pids()
        print 'uncached_pids ({}) for {} in {}'.format(len(uncached_pids), service, self.name)
        for pid in uncached_pids:
            print ' - {}'.format(pid)
            pass

    def get_pids_with_bogus_wos (self):
        bog = []
        for rec in self.data:
            if rec['wos_award_ids'] == 'AGS-1240604,CHE-1508526,NNX14AP46G,AGS-1331360':
                bog.append(rec['pid'])
        return bog

    def rid_pids_with_bogus_wos (self):
        bog = []
        lines = []
        lines.append(self.header)
        for rec in self.data:
            if rec['wos_award_ids'] == 'AGS-1240604,CHE-1508526,NNX14AP46G,AGS-1331360':
                bog.append(rec['pid'])
            else:
                lines.append(rec.data)

        print '{} bog recs found'.format(len(bog))
        print '{} records kept'.format(len(lines) -1)
        print '{} total records originally'.format(len(self.data))

        if 0:  # already done
            out_path = os.path.join (os.path.dirname(self.path), 'FILTERED.txt')
            fp = open(out_path, 'w')
            fp.write ('\n'.join (map (lambda x:'\t'.join(x), lines)))
            fp.close ()
            print 'wrote to ', out_path

        if 1:  # delete bog wos files on disk
            for pid in bog:
                filename = pid.replace (':', '_') + '.xml'
                path = os.path.join (os.path.dirname(self.path), 'metadata', 'wos', filename)
                if not os.path.exists (path):
                    print "{} does not exist".format (pid)
                else:
                    # os.remove(path)
                    pass

def compare (path1, path2):
    reader1 = AwardIdDatasetAdmin (path1)
    reader2 = AwardIdDatasetAdmin (path2)
    dups=[]

    print '{} has {} records'.format(reader1.name, len(reader1.data))
    print '{} has {} records'.format(reader2.name, len(reader2.data))


    for key in reader1.pid_map.keys():
        if key in reader2.pid_map.keys():
            dups.append (key)

    print 'dups {}'.format(len(dups))

    if 1:
        print 'NON DUPS in {} but not in DUPS'.format(reader1.name)
        for pid in reader1.pid_map.keys():
            if not pid in dups:
                print '- ',pid

    # for dup in dups:
    #     print ' -',dup

if __name__ == '__main__':
    comp_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_id_data-Composite.csv'
    partial_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/SMART_PARTIAL_v2.csv'
    doi_ref_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI_Reference_TABLE.csv'

    # reader = AwardIdDatasetReader(doi_ref_path)
    # reader.make_OPENSKY_DOIS()

