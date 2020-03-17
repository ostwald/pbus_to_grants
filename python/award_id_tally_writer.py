import sys, os, codecs, time
import urllib
sys.path.append('/Users/ostwald/devel/python-lib')

from UserList import UserList

from csv_processor import CsvReader, CsvRecord
from HyperText.HTML40 import *
from html import HtmlDocument
import navbar

class AwardIdTally:

    field = 'kuali_verified_award_ids'

    def __init__(self, path):
        self.csv = CsvReader(path)
        self.pid_map = self._get_pid_map()
        self.tally = self._get_tally()
        self.total_ids = self._get_total_ids()
        self.unique_ids = len (self.tally.keys())

    def _get_pid_map (self):
        pid_map = {}
        for rec in self.csv:
            pid_map[rec['pid']] = rec
        return pid_map

    def get_rec(self, pid):
        return self.pid_map[pid ]

    def _get_tally (self):
        tally = {}
        for record in self.csv:
            pid = record['pid']
            ids = filter (None, map (lambda x:x.strip(), record[self.field].split(',')))

            for id in ids:
                pid_list = tally.has_key(id) and tally[id] or []
                pid_list.append (pid)
                pid_list.sort()
                tally[id] = pid_list
        return tally

    def _get_total_ids (self):
        total = 0
        for key in self.tally.keys():
            total += len (self.tally[key])
        return total

    def asHtml (self):
        """
            # container  DIV#accordian
            #   header   H3
            #   content  DIV.content
            #       kuali_link   DIV.kuali-link
            #       table   (TABLE.data-table
            #           header_row (TR)
        """
        ids = filter (None, self.tally.keys())
        ids.sort(key = lambda x: -len(self.tally[x]))
        container = DIV(id="accordion")
        print len(ids), ' IDS'
        for award_id in ids:
            # print 'award_id: {}'.format(award_id)
            pids = self.tally[award_id]
            # print 'pids: {}'.format(pids)

            ## HEADER - accordion header
            header = H3 ('')
            container.append (header)

            href = 'https://stage.ucar.dgiclound.com/kuali?award_id=' + urllib.quote_plus(award_id)
            header.append(award_id)   # link to kuali API tool
            header.append(SPAN(len(pids), klass="occurs"))


            ## CONTENT - accordion content
            content = DIV(klass="content", id=award_id)
            container.append(content)

            # Kuali_LINK "see Kuali API Response for " + award_id
            kuali_link = DIV (klass="kuali-link")
            # kuali_link.append (SPAN ("See", klass="kuali-word"))
            # kuali_link.append (SPAN (A("Kuali Response", href=href, target="kuali"),
            #                             klass="award-id kuali-word"))
            kuali_link.append (BUTTON ("Kuali Response", type="button", klass="award-id kuali-word"))
            kuali_link.append (SPAN ("for {}".format(award_id), klass="kuali-word"))
            content.append(kuali_link)

            # DATA_TABLE
            table = TABLE(klass='data-table')
            header_row = TR()
            for field in ['pid', 'doi', 'pub_date']:
                header_row.append (TH (field))
            table.append (header_row)
            for pid in pids:
                normalized_pid = pid.replace (':', '_');
                rec = self.get_rec(pid)
                row = TR(id=normalized_pid, klass="pub-row")

                # PID - how to format??
                href = 'https://opensky.ucar.edu/islandora/object/'+pid.replace(':', '%3A')
                row.append (TD (A(pid, href=href, target="opensky"), klass="context-link"))

                # DOI
                doi = rec['doi']
                href = 'https://dx.doi.org/' + urllib.quote_plus(doi)
                row.append (TD (A(doi, href=href, target="doi"), klass="context-link"))

                # PUB_DATE
                row.append (TD (rec['pub_date']))

                table.append(row)

            content.append(table)
        return container

def makeHtmlDoc (tally_html):
    """
    Generate the html document as string
    """
    title = 'Kuali Match Results Tally'
    doc = HtmlDocument (title=title)
    # doc.body["onload"] = "init();"

    # <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

    doc.head.append (META(http_equiv="Content-Type",
                          content="text/html; charset=utf-8"))

    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js")
    doc.addJavascript ("https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.1/jquery-ui.min.js")
    doc.addJavascript ("tally-script.js")

    doc.addStylesheet ("//code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css")
    doc.addStylesheet ("tally-styles.css")

    doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))

    doc.append (DIV (id="debug"))

    doc.append (navbar.get_nav_bar())

    doc.append (H1 (title))

    doc.append (tally_html)

    return doc


def show_award_id_tally (tally_instance):
    tally = tally_instance.tally
    total = 0
    for key in tally.keys():
        total += len (tally[key])
    ids= tally.keys()
    print '{} unique kuali_verified_award_ids'.format(tally_instance.unique_ids)
    print '{} total kuali_verified_award_ids found'.format (tally_instance.total_ids)
    ids.sort(key = lambda x: -len(tally[x]))
    print 'AWARD ID by frequency'
    for id in ids:
        print '{} ({})'.format(id, len(tally[id]))

if __name__ == '__main__':

    path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL_AGAIN.csv'
    tally = AwardIdTally(path)

    # show_award_id_tally (tally)
    # print tally.asHtml()

    if 1:  # write tally html to disk
        doc = makeHtmlDoc (tally.asHtml())
        out_path = 'html/results-tally.html'
        fp = codecs.open(out_path, 'w', 'utf-8')

        fp.write (doc.__str__())
        fp.close()
        print 'wrote to ', out_path