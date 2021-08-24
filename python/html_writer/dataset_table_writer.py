"""
BASED ON: python/match_results_html_writer.py

consume csv file AWARD_ID_DATASET and write Match-Results html, which lists the
record's pid and DOI along with award_ids each of crossref, WOS, and Kual
 - see for an example of this output
   https://oswscl.dls.ucar.edu/kuali/match-results.html

"""
import os, sys, time, urllib, codecs
# sys.path.append('/Users/ostwald/devel/python-lib')
from slice import SliceWriter

from HyperText.HTML40 import *
from html import HtmlDocument
from python import AwardIdDatasetReader, AwardIdDatasetRecord, navbar

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

class DatasetTableRecord(AwardIdDatasetRecord):

    award_id_fields = ['wos_award_ids', 'crossref_award_ids', 'kuali_verified_award_ids']
    date_fields = ['lastmod', 'created', 'pub_date']

    def __init__ (self, data, schema):
        AwardIdDatasetRecord.__init__ (self, data, schema)
        # for name in ['created', 'pub_date', 'lastmod']:
        #     setattr(self, name+'_date', make_date_stamp(self[name]))
        #     # self.created_time = self.make_date_stamp(self['created'])

    def ashtml (self):
        row = TR(id=self['pid'].replace(':', '_'))
        for field in self.schema:

            val = self[field]
            # print ' -- val: {}'.format(val)
            # print '  -> now: {}'.format(self.makeVal(field))
            klass = field
            if field in self.date_fields:
                klass += ' ' + 'date-cell'
            row.append (TD (self.makeVal(field), klass=klass))
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
        elif field in self.award_id_fields:
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

class DatasetTableWriter(AwardIdDatasetReader):

    record_class = DatasetTableRecord
    encoding = 'utf8'
    date_fields = ['lastmod', 'created', 'pub_date']

    def __init__ (self, path, filter_args={}):
        print 'filter args: ', filter_args
        AwardIdDatasetReader.__init__(self, path, filter_args)
        self._data_table_html = None


    def get_data_table_html(self):
        if self._data_table_html is None:
            table = TABLE(klass='data-table')
            header = TR (klass='header')
            for field in self.header:
                cell = TH (field)
                if field in self.date_fields:
                    cell['klass'] = 'date-cell'
                header.append (cell)

            table.append(header)
            # self.data.sort (key=lambda x:x['pid'])
            # self.data.sort (key=pid_sort_key)

            for row in self.data:
                table.append (row.ashtml())

            try:
                table.__str__()
                print 'table is okay'
            except :
                print 'table is not okay'

            self._data_table_html = table
        return self._data_table_html


class DatasetSliceWriter (SliceWriter):

    # def __init__ (self, path, filter_args={}):
    #     SliceWriter.__init__(self, path, filter_args)

    def get_dataset(self, path, filter_args):
        return DatasetTableWriter(path, filter_args)

    def get_html_doc (self):
        """
        Generate the html document as string
        """
        data_table = self.dataset.get_data_table_html()
        doc = SliceWriter.get_html_doc (self)
        doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))
        doc.append (DIV (id="debug"))
        doc.append (navbar.get_nav_bar('match-results'))
        doc.append (H1 ('All Records'))
        doc.append (H2 (self.title))

        num_records_total = len(self.dataset.data)
        num_records_with_funding_info = len(self.dataset.get_recs_having_award_id())
        if num_records_total == 0:
            percent_finding_info = 0
        else:
            percent_finding_info = int(100 * float(num_records_with_funding_info) / num_records_total)

        all_records_stats = "{} Records, {}% have funding info".format(num_records_total, percent_finding_info)
        doc.append (DIV (all_records_stats, id="all-records-stats"))


        # doc.append (DIV( BUTTON("sort me", type="button", id="sort-button")))

        doc.append (data_table)

        return doc


    def write_html(self):
        out_path = os.path.join(self.dirname, 'match-results.html')
        fp = open(out_path,'w')
        fp.write (self.get_html_doc().__str__())
        fp.close()
        print 'wrote to ', out_path

if __name__ == '__main__':
    if 0:
        doc = get_html_doc()
        print doc.__str__()

    if 1:
        filter_args = {'start':'2020-01-01', 'end':'2020-04-30', 'date_field':'created'}
        sort_args = {'field':'created'}
        # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
        writer = DatasetSliceWriter (csv_path, filter_args)

        # records = writer.get_filtered_records(filter_fn=my_filter_fun)
        writer.write_html()




