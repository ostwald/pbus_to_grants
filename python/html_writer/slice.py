"""
Award_id_dataslice

- A slice of the Award_Id_datasSET

create Landing page for this slice

and the match-results and tally-results pages
"""

import os, sys, re, time, json
sys.path.append ('/Users/ostwald/devel/python/python-lib')
from HyperText.HTML40 import *
from html import HtmlDocument
from python import AwardIdDatasetReader, FilterSpec, navbar
import config

class SliceWriter:

    html_base = config.html_base

    def __init__(self, path, filter_args):
        """
        dataset is a AwardIdDatasetReader that represents the csv file
        at path.
        filter_args define a Slice of data to be
        :param path:
        :param filter_args:
        """
        self.dataset = self.get_dataset(path, filter_args)
        self.start = self.dataset.filter_spec.spec['start']
        self.end = self.dataset.filter_spec.spec['end']
        self.date_field = self.dataset.filter_spec.spec['date_field']
        self.name = '{}-{}-{}'.format(self.start, self.end, self.date_field)
        self.title = 'from {} to {}'.format(self.start, self.end)
        self.dirname = os.path.join (self.html_base, self.name)
        if not os.path.exists(self.dirname):
            os.mkdir (self.dirname)

    def get_dataset (self, path, filter_args):
        """
        NOTE: data is sorted by 'created' by default
        :param path:
        :param filter_args:
        :return:
        """
        sort_args = {'field':'created', 'reverse': False}
        return AwardIdDatasetReader(path, filter_args, sort_args)

    def get_html_summary_vert (self):
        """
        to be shown on TOC page
        :return:
        """
        summary = DIV(klass="slice-summary")
        # summary.append (SPAN("Start: " + self.start, klass="start"))
        # summary.append (SPAN("End: " + self.end, klass="end"))
        # summary.append (DIV(self.title, klass="title"))
        summary.append (DIV("{} to {}".format(self.start, self.end), klass="header"))

        num_records_total = len(self.dataset.data)
        num_records_with_funding_info = len(self.dataset.get_recs_having_award_id())
        num_unique_award_ids = len(self.dataset.get_unique_award_ids())
        percent_finding_info = int(100 * float(num_records_with_funding_info) / num_records_total)

        summary.append (DIV("{} Records total, {}% have funding info".format(num_records_total, percent_finding_info), klass="stat"))
        # summary.append (DIV("{} Records have finding info".format(num_records_with_funding_info), klass="stat"))
        summary.append (SPAN("There are {} unique award Ids".format(num_unique_award_ids, klass="stat")))

        nav_links = UL(klass='nav-links')
        href = '{}/results-tally.html'.format(self.name)
        # nav_links.append (A ("award ID tally", href="{}/results-tally.html".format(self.name)))
        nav_links.append (LI (A ("Award ID Tally", href=href)))
        nav_links.append (LI (' | '))
        nav_links.append (LI (A ("All Records", href="{}/results-tally.html".format(self.name))))
        summary.append (nav_links)
        return summary

    def get_summary_table_row(self):
        """

        :return: an TR row containing info about this slice as well as
        links to more detailed data
        """
        num_records_total = len(self.dataset.data)
        num_records_with_funding_info = len(self.dataset.get_recs_having_award_id())
        num_unique_award_ids = len(self.dataset.get_unique_award_ids())
        percent_finding_info = int(100 * float(num_records_with_funding_info) / num_records_total)
        award_ids_per_record = '{:.2f}'.format(float(self.dataset.get_total_award_ids()) / num_records_total)

        row = TR(
            TD(self.start),
            TD(self.end),
            TD(num_records_total),
            TD(percent_finding_info),
            TD(award_ids_per_record),
            TD(num_unique_award_ids),
            TD(A ("All Records", href="{}/match-results.html".format(self.name)), klass="link-cell"),
            TD(A ("Award ID Tally", href="{}/results-tally.html".format(self.name)))
        )

        return row

    def get_html_summary (self):
        """
        summary of slice to be shown on TOC page
        :return:
        """
        summary = DIV(klass="slice-summary")
        # summary.append (SPAN("Start: " + self.start, klass="start"))
        # summary.append (SPAN("End: " + self.end, klass="end"))
        # summary.append (DIV(self.title, klass="title"))
        summary.append (DIV("{} to {}".format(self.start, self.end), klass="header"))

        num_records_total = len(self.dataset.data)
        num_records_with_funding_info = len(self.dataset.get_recs_having_award_id())
        num_unique_award_ids = len(self.dataset.get_unique_award_ids())
        try:
            percent_finding_info = int(100 * float(num_records_with_funding_info) / num_records_total)
        except ZeroDivisionError:
            percent_finding_info = 0

        table = TABLE(klass='slice-table')
        table.append(TR (TD ("{} Records total, {}% have funding info".format(num_records_total, percent_finding_info)),
                         TD (A ("All Records", href="{}/match-results.html".format(self.name)), klass="link-cell")))

        table.append (TR (TD("There are {} unique award Ids".format(num_unique_award_ids)),
                          TD(A ("Award ID Tally", href="{}/results-tally.html".format(self.name)), klass="link-cell")))


        summary.append (table)
        return summary

    def get_html_doc(self):
        """
        This method provides the html framework, javascript and css)

        Add content like this:
           doc.append (navbar.get_nav_bar())
           doc.append (H1 (title))

        :param self:
        :param title:
        :return:
        """

        doc = HtmlDocument (title=self.title, stylesheet="../styles.css")
        # doc.body["onload"] = "init();"

        # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

        doc.head.append (META(http_equiv="Content-Type",
                              content="text/html; charset=utf-8"))

        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
        doc.addJavascript ("../script.js")
        return doc

class HomeSlice(SliceWriter):

    def get_html_doc (self):
        doc = SliceWriter.get_html_doc (self)

        doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))
        doc.append (DIV (id="debug"))
        doc.append (navbar.get_nav_bar())

        doc.append (H1 (self.title))
        table = TABLE()

        table_data = [
            ['records', len(self.dataset.data)],
            ['with award_id', len (self.dataset.get_recs_having_award_id())],
            ['unique_award_ids', len(self.dataset.get_unique_award_ids())]
        ]

        for row_data in table_data:
            tr = TR(TD (row_data[0], TD(row_data[1])))
            table.append(tr)

        doc.append(table)
        return doc

    def write_slice_data (self):
        """
        writes json representing the data for this slice, to file
        :return:
        """
        slice = self.dataset
        data = {
            'filter_spec' : slice.filter_spec.spec,
            'name' : self.name,
            'num_records' : len(slice.data),
            'num_records_with_award_id' : len(slice.get_recs_having_award_id()),
            'unique_award_ids' : len(slice.get_unique_award_ids()),
        }
        out_path = os.path.join(self.dirname, 'slice_data.json')
        fp = open(out_path,'w')
        fp.write (json.dumps(data, indent=4))
        fp.close()
        print 'wrote to ', out_path

    def write_html(self):
        out_path = os.path.join(self.dirname, 'index.html')
        fp = open(out_path,'w')
        fp.write (self.get_html_doc().__str__())
        fp.close()
        print 'wrote to ', out_path

def whole_slice_writer (csv_path, filter_args):
    from dataset_table_writer import DatasetSliceWriter
    from dataset_tally_writer import TallySliceWriter
    # dataset = AwardIdDatasetReader(csv_path, filter_args)
    slice = HomeSlice (csv_path, filter_args)
    print 'slicey at: ', slice.dirname
    slice.write_html()
    slice.write_slice_data()

    tallywriter = TallySliceWriter (csv_path, filter_args)
    tallywriter.write_html()
    tablewriter = DatasetSliceWriter (csv_path, filter_args)
    tablewriter.write_html()

def slice_series_writer ():
    from dataset_table_writer import DatasetSliceWriter
    from dataset_tally_writer import TallySliceWriter

    filter_args_list = [
        {'end':'2019-08-19', 'date_field':'created'},
        {'start':'2019-08-19', 'end':'2020-01-01', 'date_field':'created'},
        {'start':'2020-01-01', 'end':'2020-08-01', 'date_field':'created'},
    ]
    # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    for args in filter_args_list:
        whole_slice_writer(csv_path, args)

if __name__ == '__main__':

    filter_args = {'start':'2020-01-01', 'end':'2020-08-01', 'date_field':'created'}
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    whole_slice_writer(csv_path, filter_args)