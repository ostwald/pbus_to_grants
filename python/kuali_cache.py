"""
kuali cache is written by php doi_tester

the KEYS are award_ids found in metadata (including wos and crossref)
the VALUeS are Kuali_ids (or False if a kuali_id was not found)

"""
from UserDict import UserDict
import json

CACHE_PATH = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/kuali_cache.json'

class KualiCache (UserDict):

    def __init__ (self, path=None):
        if path is None:
            path = CACHE_PATH
        self.path = path
        self.data = json.loads(open(path, 'r').read())

    def find_kuali_id (self, award_id):
        """
        returns valid kuali_id associated with award_id or
        None if one cannot be fond
        :param id:
        :return:
        """
        val = None
        if self.has_key(award_id):
            val = self[award_id]
            if val == 'FALSE':
                return None
        elif award_id in self.values():
            val = award_id
        return not val and None or val

    def report (self, hits_only=False):
        for key in self.keys():
            val = self[key]
            # if (val is not None and val != 'None') or not hits_only:
            if val or not hits_only:
                print '{}: {}'.format(key, self[key])

    def show_hits(self, needle):
        for key in self.keys():
            if needle is not None and not needle in key:
                continue
            if self[key]:
                print '{}: {}'.format(key, self[key])

    def add_mapping(self, key, value, force=False):
        if not force and self.has_key(key):
            val = self[key]
            if val != value:
                raise KeyError, "{} already has different value: {}".format(key, val)
        else:
            self[key] = value
            self.write_cache_file()

    def keys(self):
        keys = self.data.keys()
        keys.sort()
        return keys

    def asTabDelimited(self, tsv_path=None):
        if tsv_path is None:
            tsv_path = '/Users/ostwald/tmp/KUALI_CACHE.tsv'
        lines = [];add=lines.append
        add ('Query_id\tKuali_id')
        for key in self.keys():
            add (u'{}\t{}'.format(key, self[key]))
        fp = open(tsv_path,'w')
        fp.write ('\n'.join (lines).encode( 'utf8'))
        fp.close()
        print 'wrote to ', tsv_path

    def write_cache_file (self):
        fp = open(self.path, 'w')
        fp.write (json.dumps(self.data, indent=2))
        fp.close()
        print 'cache updated at', self.path

    def batch_lookup (self, award_ids):
        for award_id in award_ids:
            print ' - {} - {}'.format(award_id, self.find_kuali_id(award_id))

    def cache_correction (self, csv_data):
        from csv_processor import CsvReader
        reader = CsvReader (csv_data)
        for rec in reader:
            key = rec['Award_id']
            val = rec['Notes']
            print '{} -> {}'.format(key, val)
            try:
                self.add_mapping(key, val, force=1)
            except KeyError, msg:
                print msg


if __name__ == '__main__':
    cache = KualiCache ()
    print 'cache has {} keys'.format(len(cache))
    # cache.report(hits_only=True)
    # cache.asTabDelimited()

    if 0: # tally ho
        tally = {}
        for key in cache.keys():
            tp = type(key)
            vals = tp in tally and tally[tp] or []
            vals.append(key)
            tally[tp] = vals
        for key in tally:
            print '-     {}: {}'.format(key, len(tally[key]))

    if 0: # update cache
        cache.add_mapping('-CHE1049058.00', 'CHE-1049058',1)


    if 1: # cache correction via cvs
        cvs_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Cache_Correction_from_DOI_ref.csv'
        cache.cache_correction(cvs_path)
    if 0:
        award_ids = [
            # '10121480201',
            # 'DEAC0500OR22725',
            # 'DEAC0576RL01830',
            # 'DEAC3608GO28308',
            # 'DEAC5207NA27344',
            'CHE1049058',
            'CHE-1049058'
        ]

        cache.batch_lookup(award_ids)

    if 0:
        keys = cache.keys()
        keys.sort()
        for key in keys:
            print key
    if 0:
        vals = cache.values()
        print len(vals), 'values'

    if 0:
        kuali_cache = KualiCache()
        ref_ids = ['1138784','DEAC06-76RLO','41127901','41025016','41121003','KZZD-EW-01','2012CB825605','DEAC0500OR22725']
        kuali_ids = filter (None, map (lambda x:kuali_cache.find_kuali_id(x), ref_ids))
        print kuali_ids