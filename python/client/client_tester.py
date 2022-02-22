import json
from kuali_client import KualiClient


def get_kuali_response_tester(award_id):
    print 'get_kuali_response_tester'
    client = KualiClient()
    print 'tester: {}'.format(client.get_minimal_award_id(award_id))
    for f in client.skip_award_ids:
        print f


    resp = client.get_kuali_response(award_id)
    print 'resp is a {}'.format(type (resp))
    print json.dumps(resp, indent=3)
    print '\n - {} hits for {}'.format(client.get_num_hits(award_id), award_id)


def parse_kuali_award_info_tester (award_id):
    client = KualiClient()
    kuali_resp = client.get_kuali_response(award_id)
    # print json.dumps(kuali_resp, indent=3)
    resp = client.parse_kuali_award_info (award_id, kuali_resp)
    print 'response is a {}'.format(type(resp))
    print json.dumps(resp, indent=3)

def get_kuali_award_id_tester (award_id):
    print 'AWARD_ID_TO_FIND: "{}"'.format(award_id)
    client = KualiClient()
    award_id = client.get_kuali_award_id(award_id)
    print 'AWARD_ID_FOUND: "{}"'.format(award_id)



if __name__ == '__main__':
    # award_id = 'NA13OAR4310138' # 2 hits
    # award_id = 'DE-SC0012711'  # 1 hit
    # award_id = 'SC0012711'  # 1 hit partial
    # award_id = 'SC0012711x'  # 0 hit
    # award_id = None
    # award_id = ''
    # award_id = 'DEAC0576RL01830'  # skpped
    # award_id = '1755088'  # 17 hits
    # award_id = '10167'  #
    # award_id = 'WROC10167'  #
    award_id = '10-1110-NCAR '  #

    # get_kuali_response_tester (award_id)
    # parse_kuali_award_info_tester (award_id)
    get_kuali_award_id_tester (award_id)