"""

writes a website consisting of a landing page, and providing access to several subsites,
which are called "Slices" (instances of HomeSlice)
manages the individual

"""

import os, sys, re, time, json
sys.path.append ('/Users/ostwald/devel/python/python-lib')
from HyperText.HTML40 import *
from html import HtmlDocument

from slice import HomeSlice
from dataset_table_writer import DatasetSliceWriter
from dataset_tally_writer import TallySliceWriter
import config

class SiteWriter:

    def __init__ (self, csv_path, filter_args_list):
        self.slices = []
        self.title = "Pubs 2 Grants Data Site"
        for filter_args in filter_args_list:
            homeslice = HomeSlice(csv_path, filter_args)
            self.slices.append(homeslice)
            print 'added ', homeslice.name

    def write_slice_site (self, homeslice):
        filter_args = homeslice.dataset.filter_spec.spec

        print '\nwriting slice: () filter args'.format(homeslice.name, filter_args)
        homeslice.write_html()
        homeslice.write_slice_data()
        tallywriter = TallySliceWriter (csv_path, filter_args)
        tallywriter.write_html()
        tablewriter = DatasetSliceWriter (csv_path, filter_args)
        tablewriter.write_html()

    def write_site (self):
        for homeslice in self.slices:
            # print '\nAbout to write a SLICE'
            # print homeslice.name
            # print homeslice.dataset.filter_spec.spec
            # continue
            self.write_slice_site (homeslice)

        self.write_index_html()

        print 'FINISHED writing Site'

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

        doc = HtmlDocument (title=self.title, stylesheet="styles.css")
        # doc.body["onload"] = "init();"

        # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

        doc.head.append (META(http_equiv="Content-Type",
                              content="text/html; charset=utf-8"))
        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
        doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
        doc.addJavascript ("script.js")

        doc.append (H1 ("Funding Information in OpenSky Records"))

        doc.append ("See ", A ("QA Notes (GoogleDoc)",
                   target="google_doc",
                   href="https://docs.google.com/document/d/1RIXIBJGO_PrbFnAy1r9qXTY8AjoxDI5C9rrzpO4v0z4"))

        doc.append(self.site_list_html())

        return doc

    def site_list_html (self):
        site_list = UL(id='slice-list')
        for homeslice in self.slices:
            site_list.append (LI (homeslice.get_html_summary()))
        return site_list

    def write_index_html(self):
        out_path = os.path.join(config.html_base, 'index.html')
        fp = open(out_path,'w')
        fp.write (self.get_html_doc().__str__())
        fp.close()
        print 'wrote to ', out_path

if __name__ == '__main__':

    filter_args_list = [
        {'num':1, 'end':'2019-08-19', 'date_field':'created'},
        {'num':2, 'start':'2019-08-20', 'end':'2019-12-31', 'date_field':'created'},
        {'num':3, 'start':'2020-01-01', 'end':'2020-04-30', 'date_field':'created'},
    ]
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    writer = SiteWriter(csv_path, filter_args_list)

    # doc = writer.get_html_doc ()
    # writer.write_index_html()

    for homeslice in writer.slices:
        print '{} - {}'.format(homeslice.name, homeslice.dataset.filter_spec.spec)

    writer.write_site()