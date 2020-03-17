import sys, os, codecs, time
import urllib
sys.path.append('/Users/ostwald/devel/python-lib')

from csv_processor import get_unique_values, CsvReader

from client import KualiClient
from HyperText.HTML40 import *
from html import HtmlDocument
import navbar


"""

"""
class KualiResultTally:
    """
    tally - a mapping from award_id to the number of hits it returns in the kuali API
    """

    verbose = False

    def __init__ (self, csv_path):
        self.tally = None
        self.kuali = KualiClient ()
        self.award_ids = get_unique_values(csv_path, 'kuali_verified_award_ids')
        print '{} award ids found'.format(len (self.award_ids))

    def get_kuali_hits (self, award_id):
        return self.kuali.get_num_hits(award_id)

    def process (self):
        """
        set up the tally mapping - a
        :return:
        """
        self.tally = {}
        for id in self.award_ids:
            num_hits = self.get_kuali_hits(id)
            self.tally[id] = num_hits
            # print ' - {} ({})'.format(id, num_hits)

        # overwrite the award_ids to be sorted by num_its

        self.award_ids = self.tally.keys()
        self.award_ids.sort(key=lambda x:-self.tally[x])

        if self.verbose:
            for key in self.award_ids:
                print '- {} ({})'.format(key, self.tally[key])

    def asHtml (self):
        """
            # container  DIV#accordian
            #   header   H3
            #   content  DIV.content
            #       kuali_link   DIV.kuali-link
            #       table   (TABLE.data-table
            #           header_row (TR)
        """

        container = DIV(id="kuali-api-tally")
        for award_id in self.award_ids[:5]:
            # print 'award_id: {}'.format(award_id)
            pids = self.tally[award_id]
            print 'pids: {}'.format(pids)

            record = DIV (klass='award-id', id=award_id)


            href = 'https://osstage2.ucar.edu/kuali?award_id=' + urllib.quote_plus(award_id)
            link = A(award_id, href=href, target="opensky", klass="kuali-api-link")
            hit_count = DIV(self.tally[award_id], klass="kuali-api-hit-count")
            record.append (link, hit_count)

            container.append (record)

        return container

def makeHtmlDoc (tally_html):
    """
    Generate the html document as string
    """
    title = 'Kuali API Results Tally'
    doc = HtmlDocument (title=title)
    # doc.body["onload"] = "init();"

    # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

    doc.head.append (META(http_equiv="Content-Type",
                          content="text/html; charset=utf-8"))

    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
    # doc.addJavascript ("tally-script.js")

    doc.addStylesheet ("//code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css")
    doc.addStylesheet ("tally-styles.css")

    doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))

    doc.append (DIV (id="debug"))

    doc.append (navbar.get_nav_bar())

    doc.append (H1 (title))

    doc.append (tally_html)

    return doc

if __name__ == '__main__':
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL_AGAIN.csv'
    tally = KualiResultTally(csv_path)
    print 'processing ...'
    tally.process()
    print str(tally.asHtml())

    if 0: # write kuali api tally html
        doc = makeHtmlDoc (tally.asHtml())
        out_path = 'html/kuali-api-tally.html'
        fp = codecs.open(out_path, 'w', 'utf-8')

        fp.write (doc.__str__())
        fp.close()
        print 'wrote to ', out_path
