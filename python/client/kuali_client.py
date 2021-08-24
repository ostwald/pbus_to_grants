import sys, re
import json
import requests
from requests.auth import HTTPBasicAuth

sys.path.append ('/Users/ostwald/devel/opensky/pubs_to_grants')
from python.client import config

class KualiClientException (Exception):
    pass

class KualiClient:

    username = config.username
    password = config.password
    raw_skip_award_ids = config.skip_award_ids

    sanitize_pat = re.compile('[^A-Za-z0-9 ]')
    three_letter_start_pat = re.compile('[a-zA-Z]{3}')


    def __init__ (self, base_url=None):
        self.base_url = base_url is not None and base_url or config.production_base_url
        self.skip_award_ids = self.make_skip_list()

    def make_skip_list (self):
        skippers = []
        for id in self.raw_skip_award_ids:
            skippers.append (self.get_minimal_award_id(id))
        return skippers

    def sanitize_id (self, id):
        """
        Remove all chars that are not letters or numbers
        :param id:
        :return:
        """
        return re.sub (self.sanitize_pat, '', id)

    def get_kuali_award_id (self, award_id):
        """
        Get the Kuali API award_id for the specified version (or null if Kuali cannot
        recognize the given award_id. Sometimes the Kuail
        id is different, so this is a way to get the Kuali Id so we can use it
        :param award_id:
        :return:
        """
        # print '\nget_kuali_award_id: award_id = {}'.format(award_id)
        info = self.get_kuali_award_info(award_id)
        # print 'info is a {}'.format(type(info))
        # print json.dumps(info, indent=3)

        """
        if info is not None:
            # on a total whiff, the fainId field is none
            if info['fainId'] == 'none':
                print 'MISS'
                return None

            for field in ['sponsorAwardId', 'fainId']:
                if info[field] is None:
                    continue
                sought_id = self.sanitize_id(info[field])
                test_id = self.sanitize_id(award_id)

                # kludge for when the ids only differ but a 3-char prefix
                if three_letter_start_pat.match(test_id[:3]):
                    test_id = test_id[3:]


                # print 'sought: "{}"  test: "{}"'.format(sought_id,test_id)
                if sought_id.endswith (test_id):
                    return info[field]

                if test_id.endswith (sought_id):
                    return info[field]

        # print 'not found'
        return None
        """
        return self.find_kuali_id_in_result(award_id, info)

    def find_kuali_id_in_result(self, award_id, info):

        # on a total whiff, the fainId field is none
        if info['fainId'] == 'none':
            print 'MISS'
            return None

        for field in ['sponsorAwardId', 'fainId']:
            if info[field] is None:
                continue
            sought_id = self.sanitize_id(info[field])
            test_id = self.sanitize_id(award_id)

            # kludge for when the ids only differ but a 3-char prefix
            if self.three_letter_start_pat.match(test_id[:3]):
                test_id = test_id[3:]


            # print 'sought: "{}"  test: "{}"'.format(sought_id,test_id)
            if sought_id.endswith (test_id):
                return info[field]

            if test_id.endswith (sought_id):
                return info[field]

    def get_minimal_award_id(self, award_id):
        """
        Kuali only matches the last 5 characters, so a minimal version of a given award_id
        takes the last 5 chars  of the given award_id after sanitizing it.
        :param award_id:
        :return:
        """
        return self.sanitize_id(award_id)[-5:].upper()

    def accept_award_id(self, award_id):
        """
        Test given award_id against the skip_award_ids in config
        :param award_id:
        :return:
        """
        return not self.get_minimal_award_id(award_id) in self.skip_award_ids

    def get_kuali_response (self, award_id):
        """
        returns a list of hits from kuali APIf
        :param award_id:
        :return:
        """

        # print 'get_kuali_response: "{}"'.format(award_id)
        # print 'url: {}'.format(self.base_url)

        # problem: award_id may not be "normalized" yet
        if not self.accept_award_id (award_id):
            return None

        try:
            if award_id is None:
                raise KualiClientException, 'Sponsor Award ID parameter is empty'

            url = "{}?sponsorAwardId={}".format(self.base_url, award_id)

            resp = requests.get (url, auth=HTTPBasicAuth(self.username, self.password))

            #    print 'GET {}'.format(pid)
            #    print resp.status_code

            return resp.json()
        except Exception, msg:
            # print 'msg is a {}'.format(type (msg))
            # print (dir (msg))
            return {'message' : msg.message}
            # return {'message' : "hello"}


    def get_num_hits(self, award_id):
        try:
            return len(self.get_kuali_response(award_id))
        except Exception, msg:
            # print 'ERROR ({}): {}'.format(award_id, msg)
            return 0

    def get_kuali_award_info(self, award_id):
        resp = self.get_kuali_response(award_id)

        # print 'get_kuali_award_info: resp\n{}'.format(json.dumps(resp, indent=3))
        # return self.parse_kuali_award_info(award_id, resp)

        award_info = self.parse_kuali_award_info(award_id, resp)
        return award_info

    def parse_kuali_award_info (self, award_id, results):
        # print 'results is a {}'.format(type(results))
        if results is None:
            return None

        if type(results) == type ({}):
            # print json.dumps(results, indent=3)
            if results.has_key('message'):
                return None

        elif type(results) == type([]):
            # print 'there are {} results to parse'.format(len(results))

            for result in results:
                if result.has_key('matchType') and result['matchType'] == 'full':
                    return result

            # get kuali's version of the award_id, not necessarily what we searched for (sought)
            for result in results:
                award_id = self.find_kuali_id_in_result(award_id, result)
                if award_id is not None:
                    return result
                """
                fields_to_check = ['sponsorAwardId', 'fainId']
                for field in fields_to_check:
                    if result[field] is None:
                        continue
                    kuali_award_id = self.sanitize_id (result[field])
                    sought_award_id = self.sanitize_id (award_id)

                    extra = len (sought_award_id) - len(kuali_award_id)
                    if extra > 0:
                        sought_award_id = sought_award_id[extra:]

                    # if sought_award_id.startswith("AGS"):
                    #     sought_award_id = sought_award_id[3:]

                    if kuali_award_id.endswith(sought_award_id):
                        # print '\n{} - partial match with {} field'.format(award_id, field)
                        return result
                """
        else:
            print 'could not process results ({})'.format(type(results))

def tester (award_id):

    client = KualiClient()
    resp = client.get_kuali_response(award_id)
    print json.dumps(resp, indent=3)
    print '\n - {} hits for {}'.format(client.get_num_hits(award_id), award_id)

    selected_award_info = client.get_kuali_award_info(award_id)
    print 'award_info: ', json.dumps(selected_award_info, indent=3)

    if selected_award_info:
        kuali_award_id = client.get_kuali_award_id(award_id)
        print 'verified kuali award_id:', kuali_award_id

if __name__ == '__main__':

    if 1:
        # award_id = '23-489' # yes
        # award_id = 'AGS0856145' # yes
        award_id = '01830' # yes
        # award_id = 'AGS0856145' # yes
        # award_id = 'N999999' # no
        # award_id = '1755088' # no
        # award_id = 'DEAC0576RL01830' # yes
        tester (award_id)


    if 0:
        client = KualiClient()

        ids = [
            'AGS1502208',
            'AGS1522830',
            'AGS1660587',
            'AGS0745337',
            'AGS0856145',
        ]
        for award_id in ids:
            kuali_award_id = client.get_kuali_award_id(award_id)
            print 'raw id: {} verified kuali id: {}'.format(award_id, kuali_award_id)