
# security for kuali API - do not manage in Git

# base_url = 'http://fatomcat.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid'
# base_url = 'http://fatomcat-test.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid'
base_url = 'https://www.fin.ucar.edu/kualiapi/awardsbysponsorawardid'
username = 'openskykcapi'
password = 'W!n+er5now#'

# we do not supply kuali info for these numbers becase there are too
# many matches to make sense
skip_award_ids = [
    'DEAC0576RL01830',
    '99999',
    '0856145',
    'DTFAWA15D00036',
    '1755088',
]