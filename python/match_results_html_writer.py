"""
consume csv file AWARD_ID_DATASET and write Match-Results html, which lists the
record's pid and DOI along with award_ids each of crossref, WOS, and Kual
 - see for an example of this output
   https://oswscl.dls.ucar.edu/kuali/match-results.html

"""
import sys, time, urllib, codecs
# sys.path.append('/Users/ostwald/devel/python-lib')

import navbar

from HyperText.HTML40 import *
from html import HtmlDocument
from csv_reader import CsvRecord, CsvReader
from filtering_cvs_reader import FilteringCsvReader
from award_id_dataset_csv_reader import AwardIdDatasetReader, AwardIdDatasetRecord

def make_date_stamp (self, date_str, date_fmt="%m/%d/%y"):
    """
    in_fmt = '%m/%d/%y'
    out_fmt = '%Y-%m-%d'
    """
    try:
        t = time.strptime(date_str, in_fmt)
        return int(time.mktime(t))
    except ValueError, msg:
        print 'WARN: record {}: {}'.format(self['pid'], msg)
        return 0

class GrantInfoHtmlRecord(AwardIdDatasetRecord):

    def __init__ (self, data, schema):
        AwardIdDatasetRecord.__init__ (self, data, schema)
        # for name in ['created', 'pub_date', 'lastmod']:
        #     setattr(self, name+'_date', make_date_stamp(self[name]))
        #     # self.created_time = self.make_date_stamp(self['created'])


    def tohtml (self):
        row = TR()
        for field in self.schema:

            val = self[field]
            # print ' -- val: {}'.format(val)
            # print '  -> now: {}'.format(self.makeVal(field))

            row.append (TD (self.makeVal(field), klass=field))
        return row

    def makeVal (self, field):
        if field == 'pid':
            pid = self[field]
            href = 'https://opensky.ucar.edu/islandora/object/'+urllib.quote_plus(pid)
            return A(pid, href=href, target="opensky")
        elif field == 'doi':
            doi = self[field]
            href = 'https://dx.doi.org/' + urllib.quote_plus(doi)
            return A(doi, href=href, target="doi")
        elif field == 'pub_date':
            return self[field]
        elif field in ['wos_award_ids', 'crossref_award_ids', 'kuali_verified_award_ids']:
            ids = filter (None, map (lambda x:x.strip(), self[field].split(',')))
            container = UL(klass='award-id-list')
            for id in sorted(ids):
                href = None
                try:
                    href = 'https://stage.ucar.dgicloud.com/kuali?award_id=' + urllib.quote_plus(id)
                except:
                    print 'WARN: could not quote "{}"'.format(id.encode('utf8'))
                    sys.exit()

                if href is not None:
                    list_item = LI (A(id, href=href, target="kuali"))
                    container.append (list_item)
            return container
        return self[field]

# def my_filter_fun (rec):
#
#     if rec['pub_date'] < '2020-01-01':
#         return False
#     if rec['pub_date'] >= '2020-02-01':
#         return False
#     return True

class GrantInfoHtmlWriter(AwardIdDatasetReader):

    record_class = GrantInfoHtmlRecord
    encoding = 'utf8'

    def __init__ (self, path, filter_args={}, sort_args={}):
        self._data_table_html = None
        FilteringCsvReader.__init__ (self, path, filter_args, sort_args)

    # def get_filtered_records (self, filter_fn=None):
    #     if filter_fn is None:
    #         return self.data
    #     return filter (filter_fn, self.data)
    #     # return filter (lambda x:x['pub_date'].startswith('2020'), self.data)
    #     #return filter (lambda x:x['pub_date']  >= '2020-01-01' and x['pub_date'] < '2020-02-01', self.data)

    def get_data_table_html(self):
        if self._data_table_html is None:
            table = TABLE(klass='data-table')
            header = TR (klass='header')
            for field in self.header:
                header.append (TH (field))
            table.append(header)
            # self.data.sort (key=lambda x:x['pid'])
            # self.data.sort (key=pid_sort_key)

            for row in self.data:
                table.append (row.tohtml())

            try:
                table.__str__()
                print 'table is okay'
            except :
                print 'table is not okay'

            self._data_table_html = table
        return self._data_table_html

    def makeHtmlDoc (self):
        """
        Generate the html document as string
        """
        data_table = self.get_data_table_html()

        title = 'Kuali Smart-Match Results'
        doc = HtmlDocument (title=title, stylesheet="styles.css")
        # doc.body["onload"] = "init();"

        # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

        doc.head.append (META(http_equiv="Content-Type",
                              content="text/html; charset=utf-8"))

        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
        doc.addJavascript ("script.js")

        doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))

        doc.append (DIV (id="debug"))

        doc.append (navbar.get_nav_bar())

        doc.append (H1 (title))

        doc.append (DIV (A ("About this table", href="about.html"), id="about-link"))

        doc.append (DIV( BUTTON("sort me", type="button", id="sort-button")))

        doc.append (data_table)

        return doc

    def writeto(self, records=None, out_path='html/MATCH-RESULTS.html'):
        # out_path = 'html/match-results.html'
        fp = codecs.open(out_path, 'w', 'utf-8')
        doc = self.makeHtmlDoc()
        fp.write (doc.__str__())
        fp.close()
        print 'wrote to ', out_path


if __name__ == '__main__':
    if 0:
        doc = makeHtmlDoc()
        print doc.__str__()


    if 1:
        filter_args = {'start':'2020-01-01', 'end':'2020-08-01', 'date_field':'created'}
        sort_args = {'field':'created'}
        # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
        writer = GrantInfoHtmlWriter (csv_path, filter_args, sort_args)
        # records = writer.get_filtered_records(filter_fn=my_filter_fun)
        writer.writeto()
        # print '{} filtered records'.format(len(records))
        #
        # records.sort (key=lambda x:x['pub_date'])
        # for rec in records:
        #     print rec['pub_date']



