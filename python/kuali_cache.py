"""
kuali cache is written by php doi_tester
"""
import json

CACHE_PATH = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/kuali_cache.json'

def get_cache (path=None):
    if path is None:
        path = CACHE_PATH
    return json.loads(open(path, 'r').read())

def show_cache (path=None):
    cache = get_cache(path)
    for key in cache.keys():
        print '{}: {}'.format(key, cache[key])

def show_cache_hits (needle=None, path=None):
    cache = get_cache(path)
    for key in cache.keys():
        if needle is not None and not needle in key:
            continue
        if cache[key]:
            print '{}: {}'.format(key, cache[key])

def show_cache_size(path=None):
    size = len(get_cache(path).keys())
    print 'cache has {} keys'.format(size)

if __name__ == '__main__':

    show_cache_hits(needle='22725')
    # show_cache_size()