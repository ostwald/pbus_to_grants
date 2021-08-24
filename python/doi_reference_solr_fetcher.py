
"""
Do a solr query and return solr records object.

"""
import sys, os, re, time, traceback
from lxml import etree as ET
import requests
from ncarlibadmin import CONFIG
# from ncarlibadmin.model import FedoraObject
from ncarlibadmin.islandora_client import IslandoraObject
from back_fill import NotesMODS
from ncarlibadmin.solr import SolrResult, SolrRequest, SolrResponseDoc, SolrObjectFetcher, FieldHelper

def getFieldHelper():
    """
    These are the fields to be returned in the solr response
    :return:
    """
    fieldspec = [
        ['doi', 'mods_identifier_doi_ms'],
        ['pid', 'PID'],
        ['pub_date','keyDate'],
        ['created', 'fgs_createdDate_dt'],
        ['lastmod', 'fgs_lastModifiedDate_dt'],
        ['award_ids', 'mods_note_funding_ms'],
        ['legacy_award_ids', 'mods_note_funding_displayLabel_ms'],
    ]
    return FieldHelper(fieldspec)

def get_cataloged_kuali_award_ids (pid, rec=None):
    """
    we don't want the legacy award_ids (i.e., elements with 'displayLabel')
    :param pid:
    :return:
    """
    # pid = 'articles:22589'
    # fedoraObj = FedoraObject (pid)
    # mods_xml = fedoraObj.get__MODS_stream()
    # rec = NotesMODS (mods_xml, pid)

    if rec is None:
        obj = IslandoraObject (pid)
        rec = NotesMODS(obj.get_mods_datastream(), pid)
    all_notes = rec.get_funding_notes()
    # print '{} notes found'.format(len(all_notes))
    kuali_notes = map(lambda x:x.text,
                      filter (lambda x:x.get('displayLabel') is None, all_notes))
    return kuali_notes

def get_cataloged_legacy_award_ids (pid, rec=None):
    """
    here we ONLY want the legacy award_ids (i.e., elements with 'displayLabel')
    :param pid:
    :return:
    """
    # pid = 'articles:22589'
    # fedoraObj = FedoraObject (pid)
    # mods_xml = fedoraObj.get__MODS_stream()
    # rec = NotesMODS (mods_xml, pid)

    if rec is None:
        obj = IslandoraObject (pid)
        rec = NotesMODS(obj.get_mods_datastream(), pid)

    all_notes = rec.get_funding_notes()
    # print '{} notes found'.format(len(all_notes))
    kuali_notes = map(lambda x:x.text,
                      filter (lambda x:x.get('displayLabel') is not None, all_notes))
    return kuali_notes

class FetcherSolrResult (SolrResult):

    date_fields = ['created', 'pub_date','lastmod']
    date_pat = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')

    def __init__ (self, root):
        self._mods = None
        SolrResult.__init__(self, root)
        for spec in self.fieldHelper.fieldSpec:
            setattr(self, spec[0], self.getFieldValue(spec[1]))
        # self.pid = self.getFieldValue('PID')


    def getFieldHelper(self):
        return getFieldHelper()

    def getFieldValue(self, field):
        if not self.has_key(field):
            return ''
        val = self[field]
        if field == 'mods_note_funding_ms' and len(val) > 0:
            return ','.join(get_cataloged_kuali_award_ids(self.pid, self.get_mods()))
        if field == 'mods_note_funding_displayLabel_ms' and len(val) > 0:
            return ','.join(get_cataloged_legacy_award_ids(self.pid, self.get_mods()))

        if type(val) == type([]):
            return val[0]
        return val

    def get_mods(self):
        if self._mods is None:
            obj = IslandoraObject (self.pid)
            self._mods = NotesMODS(obj.get_mods_datastream(), self.pid)
        return self._mods

    def asTabDelimited(self):
        vals = []
        for field in map(lambda x:x[0], self.fieldHelper.fieldSpec):
            # print '{}: {}'.format(field, getattr( self, field))
            val = getattr( self, field)
            if field in self.date_fields:
                val = self.normalize_date(val)
            vals.append(val)
        return '\t'.join (vals)

    def normalize_date(self, date_str):
        m = self.date_pat.match(date_str)
        if not m:
            return date_str
        date_str = m.group()
        iso_fmt = '%Y-%m-%d'
        informal_fmt = '%-m/%-d/%y'
        date_obj = time.strptime(date_str, iso_fmt)
        return time.strftime(iso_fmt, date_obj)


class FetcherResponseDoc (SolrResponseDoc):
    result_constructor = FetcherSolrResult

    def __init__ (self, xml):
        SolrResponseDoc.__init__(self, xml)

class FetcherRequest(SolrRequest):

    result_constructor = FetcherResponseDoc

    def __init__ (self, _params={}, baseUrl=None):
        SolrRequest.__init__(self, _params, baseUrl)

    def getFieldHelper(self):
        return getFieldHelper()

    def get (self):
        try:
            r = requests.get (self.baseUrl, params=self.params)
        except Exception, msg:
            raise Exception, "request Error: %s" % msg
        # print r.url
        # print r.text
        try:
            return FetcherResponseDoc (r.text)

        except KeyError, msg:
            print 'FetcherResponseDoc ERROR: %s' % msg
            traceback.print_exc()
            pass

class Fetcher(SolrObjectFetcher):
    batch_size = 1000
    max_to_process = 100
    default_params = {
        'sort': 'PID asc'
    }
    request_class_constructor = FetcherRequest

    def __init__ (self, args):
        SolrObjectFetcher.__init__(self, args)

    def asTabDelimted (self):
        records = []
        ## HEADER GOES HERE
        header = '\t'.join (map(lambda x:x[0], getFieldHelper().fieldSpec))
        records.append (header)

        for result in self.results:
            # result is a FetcherSolrResult
            records.append (result.asTabDelimited())
        return u'\n'.join(records)

def get_args():
    query = 'mods_identifier_doi_mt:*'
    # query = 'mods_note_funding_displayLabel_ms:*'
    query += ' AND keyDate:[2014-01-01T00:00:00Z TO *]'
    # query += ' AND mods_note_funding_displayLabel_ms:*'
    query += ' AND mods_note_funding_ms:*'
    # query += ' AND fgs_createdDate_dt:[2020-04-02T00:00:00Z TO *]'
    # query += ' AND fgs_createdDate_dt:[2021-01-08T00:00:00Z TO *]'
    return {
        'params' : {
            # 'q' : 'mods_extension_collectionKey_ms:technotes',
            'q' : query,
            'rows' : '10',
            'wt': 'xml',
            'indent': 'true'
        },
         'baseUrl' : CONFIG.get("fedora", "SERVER") + CONFIG.get("fedora", "SOLR_PATH"),
    }

def requestTester ():
    query = 'mods_identifier_doi_mt:*'
    query += ' AND fgs_createdDate_dt:[2014-01-01T00:00:00Z TO *]'
    params = {
        # 'q' : 'PID:"articles:22793"',
        'q' : query,
        'rows' : '10',
        'wt': 'xml',
        'indent': 'true'
    }
    baseUrl = CONFIG.get("fedora", "SERVER") + CONFIG.get("fedora", "SOLR_PATH")
    request = FetcherRequest(params, baseUrl)
    if 0: # verbose
        print "\nrequest params"
        request.showParams()
        print ''

    doc = request.responseDoc
    if doc is None:
        raise Exception ('could not process response')
    # print doc.raw
    print '%d results in resultDoc' % len(doc.data)

    # print 'RESPONSE XML'
    # # print doc.raw
    # print ET.tostring(doc.root, pretty_print=True)

    for result in doc:
       print result.asTabDelimited()

def update_DOI_Reference ():
    fetcher = Fetcher(get_args())
    fetcher.process()
    print 'total numResults: {}'.format(fetcher.numResults)
    print 'fetched: {}'.format(len(fetcher.results))
    tab_delimited = fetcher.asTabDelimted()
    print tab_delimited
    # print 'tab_delimited is a {}'.format(type (tab_delimited))

    if 1:
        out_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/tmp/DOI-LEGACY-REFERENCE_TABLE.tsv'
        fp = open(out_path, 'w')
        fp.write (tab_delimited.encode('utf8'))
        fp.close()
        print 'wrote to {}'.format(out_path)


if __name__ == '__main__':
    # requestTester()
    update_DOI_Reference()
    # update_LEGACY_DOI_Reference()
