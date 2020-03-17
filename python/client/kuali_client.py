import sys, re
import json
import requests
from requests.auth import HTTPBasicAuth

from python.client import config

class KualiClientException (Exception):
    pass

class KualiClient:

    base_url = config.base_url
    username = config.username
    password = config.password
    raw_skip_award_ids = config.skip_award_ids

    sanitize_pat = re.compile('[^A-Za-z0-9 ]')


    def __init__ (self):
        self.skip_award_ids = self.make_skip_list()

    def make_skip_list (self):
        skippers = []
        for id in self.raw_skip_award_ids:
            skippers.append (self.get_minimal_award_id(id))
        return skippers

    def sanitize_id (self, id):
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

        if info is not None:
            if info['fainId'] == 'none':
                print 'MISS'
                return None

            for field in ['sponsorAwardId', 'fainId']:
                sought_id = self.sanitize_id(info[field])
                test_id = self.sanitize_id(award_id)

                # print 'sought: "{}"  test: "{}"'.format(sought_id,test_id)
                if sought_id.endswith (test_id):
                    return info[field]

        # print 'not found'
        return None

    def get_minimal_award_id(self, award_id):
        return self.sanitize_id(award_id)[-5:].upper()

    def accept_award_id(self, award_id):

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
                fields_to_check = ['sponsorAwardId', 'fainId']
                for field in fields_to_check:
                    kuali_award_id = self.sanitize_id (result[field])
                    sought_award_id = self.sanitize_id (award_id)

                    extra = len (sought_award_id) - len(kuali_award_id)
                    if extra > 0:
                        sought_award_id = sought_award_id[extra:]

                    if kuali_award_id.endswith(sought_award_id):
                        # print '\n{} - partial match with {} field'.format(award_id, field)
                        return result

        else:
            print 'could not process results ({})'.format(type(results))

if __name__ == '__main__':
    award_id = '23489'
    client = KualiClient()
    resp = client.get_kuali_response(award_id)
    print json.dumps(resp, indent=3)
    print '\n - {} hits for {}'.format(client.get_num_hits(award_id), award_id)