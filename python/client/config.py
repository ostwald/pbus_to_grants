
# security for kuali API - do not manage in Git

# base_url = 'http://fatomcat.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid'
sandbox_base_url = 'http://fatomcat-test.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid'
production_base_url = 'https://www.fin.ucar.edu/kualiapi/awardsbysponsorawardid'
username = 'openskykcapi'
password = 'W!n+er5now#'

# we do not supply kuali info for these numbers because there are too
# many matches to make sense
skip_award_ids = [
    '01830',    # Kuali matches to specific PNNL subawards, so nbot approp for NCAR work
    '99999',              # used as "unknown value, matches many many"

    ## numbers below were originally skipped, but now we catalog them (but do not display 'funder name' because
    ## we cannot confidenty disabmiguate from the many, many matches
    # '0856145',          # NCAR Cooperative Agreement for 2008-2018
    # 'DTFAWA15D00036',   #sposorName is DOT-FAA, but many differebnt titles
    # '1755088',          # Management and Operation of the National Center for Atmospheric Research, 2018-2023
]
