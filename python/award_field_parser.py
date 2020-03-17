"""
first, use csv_processor to grab all the award ID values found for our set of 200 pubs with DOIs

Then experiment with parsing the wordy ones into award ids

Also experiment with knocking the letter prefixes off the NSF grants
"""

import sys, os, re
from csv_processor import get_unique_values


# path = '/Users/ostwald/devel/opensky/pubs_to_grants/DOI-based_Testing/March 2018 - Exact Match/200_DOI_Kuali_Tested.csv'
path = '/Users/ostwald/devel/opensky/pubs_to_grants/DOI-based_Testing/Kuali_Client_Testing/v5/V5-SMART_PARTIAL.csv'
fields = [
    'wos_award_ids',
    'crossref_award_ids'
]

def get_wos_values():
    return get_unique_values (path, fields[0])

def get_crossref_values():
    return get_unique_values (path, fields[1])

# award_pat = re.compile ()
no_specials_pat = re.compile('[\W_-]', re.UNICODE)
num_pat = re.compile ('[0-9]', re.UNICODE)

def get_award_id (value):

    val = no_specials_pat.sub('', value)
    if len(val) < 5:
        return None

    # if it doesn't have a number, reject it
    if not num_pat.search(val):
        return None


    # has_numeric =

    return val

def get_award_id_tokens(val):
    """
    split on spaces and keep only values that could be awardIds
    """
    return filter (None, map (get_award_id, val.split(' ')))

def get_award_id_tokens_tester():
    vals = get_crossref_values()
    for val in vals:
        print val
        print ' - %s' % get_award_id_tokens(val)

if __name__ == '__main__':
    # val = 'Program Element 0601153N_-^(*'
    # print ' - %s' % get_award_id_tokens(val)

    get_award_id_tokens_tester()