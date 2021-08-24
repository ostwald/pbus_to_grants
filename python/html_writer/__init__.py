"""
Award_id_dataslice

- A slice of the Award_Id_datasSET

create Landing page for this slice

and the match-results and tally-results pages
"""

import os, sys, re
sys.path.append ('/Users/ostwald/devel/python/python-lib')
from HyperText.HTML40 import *
from html import HtmlDocument
from python import AwardIdDatasetReader, FilterSpec


# THIS CODE IS OBSOLETE AND SHOULD BE REMOVED

def makeHtmlDoc(title):
    """
    Add content like this:
       doc.append (navbar.get_nav_bar())
       doc.append (H1 (title))

    :param self:
    :param title:
    :return:
    """

    doc = HtmlDocument (title=title, stylesheet="styles.css")
    # doc.body["onload"] = "init();"

    # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

    doc.head.append (META(http_equiv="Content-Type",
                          content="text/html; charset=utf-8"))

    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
    doc.addJavascript ("script.js")

    return doc


class Slice (AwardIdDatasetReader):

    html_base = '/Users/ostwald/devel/opensky/pubs_to_grants/python/html'

    def __init__(self, path, filter_args, ):
        AwardIdDatasetReader.__init__(self, path, filter_args)
        self.name = '{}-{}-{}'.format(self.filter_spec.spec['start'],
                                       self.filter_spec.spec['end'],
                                       self.filter_spec.spec['date_field'])
        self.title = 'from {} to {}'.format(self.filter_spec.spec['start'],
                                            self.filter_spec.spec['end'])
        self.dirname = os.path.join (self.html_base, self.name)
        if not os.path.exists(self.dirname):
            os.mkdir (self.dirname)

    def getHtmlDoc (self):
        doc = makeHtmlDoc (self.title)
        doc.append (H1 (self.title))
        table = TABLE()

        table_data = [
            ['records', len(self.data)],
            ['with award_id', len (self.get_recs_having_award_id())],
            ['unique_award_ids', len(self.get_unique_award_ids())]
        ]

        for row_data in table_data:
            tr = TR(TD (row_data[0], TD(row_data[1])))
            table.append(tr)

        doc.append(table)
        return doc

    def write_html(self):
        out_path = os.path.join(self.dirname, 'index.html')
        fp = open(out_path,'w')
        fp.write (self.getHtmlDoc().__str__())
        fp.close()
        print 'wrote to ', out_path

if __name__ == '__main__':
    filter_args = {'start':'2020-01-01', 'end':'2020-08-01', 'date_field':'created'}
    sort_args = {'field':'created'}
    # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
    # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    slice = Slice (csv_path, filter_args)
    print 'slice at: ', slice.dirname
    slice.write_html()