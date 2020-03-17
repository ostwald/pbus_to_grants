import sys, time, urllib, codecs
import navbar

sys.path.append('/Users/ostwald/devel/python-lib')

from HyperText.HTML40 import *
from html import HtmlDocument
from grant_info_csv_reader import CsvRecord, CsvReader

class GrantInfoCvsRecord(CsvRecord):

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
                    href = 'https://osstage2cl.dls.ucar.edu/kuali?award_id=' + urllib.quote_plus(id)
                except:
                    print 'WARN: could not quote "{}"'.format(id.encode('utf8'))
                    sys.exit()

                if href is not None:
                    list_item = LI (A(id, href=href, target="kuali"))
                    container.append (list_item)
            return container
        return self[field]

class GrantInfoCsvReader(CsvReader):

    record_class = GrantInfoCvsRecord
    encoding = 'utf8'

    def get_data_table(self):
        table = TABLE(klass='data-table')
        header = TR (klass='header')
        for field in self.header:
            header.append (TH (field))
        table.append(header)

        def pid_sort_key (x):
            if 'pid' in x.schema:
                return x['pid']
            else:
                # print 'no pid?? %s' % x
                return ''

        # self.data.sort (key=lambda x:x['pid'])
        # self.data.sort (key=pid_sort_key)

        for row in self.data:
            table.append (row.tohtml())

        try:
            table.__str__()
            print 'table is okay'
        except :
            print 'table is not okay'

        return table



def makeHtmlDoc (data_table):
    """
    Generate the html document as string
    """
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

if __name__ == '__main__':
    if 0:
        doc = makeHtmlDoc()
        print doc.__str__()

    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
    reader = GrantInfoCsvReader (csv_path)

    print '{} rows read'.format (len(reader.data))

    doc = makeHtmlDoc (reader.get_data_table())
    out_path = 'html/match-results.html'
    fp = codecs.open(out_path, 'w', 'utf-8')

    fp.write (doc.__str__())
    fp.close()
    print 'wrote to ', out_path