"""
BASED ON: python/result_tally_html_writer.py

write results-tally, which lists the unique award_ids for records within the specified
data range. award_ids are listed in order of frequency, with links to the individual records that
are asosociated with each award_id
 - see for an example of this output
   https://oswscl.dls.ucar.edu/kuali/results-tally.html

"""
import os, sys, time, urllib, codecs
# sys.path.append('/Users/ostwald/devel/python-lib')
from slice import SliceWriter

from HyperText.HTML40 import *
from html import HtmlDocument
from python import AwardIdDatasetReader, AwardIdDatasetRecord, navbar

class DatasetTallyRecord(AwardIdDatasetRecord):

    def ashtml (self):
        """

        :return: and instance of TR describing this record
        """
        pid = self['pid']
        normalized_pid = pid.replace (':', '_');
        row = TR(id=normalized_pid, klass="pub-row")

        # PID - how to format??
        href = 'https://opensky.ucar.edu/islandora/object/'+pid.replace(':', '%3A')
        row.append (TD (A(pid, href=href, target="opensky"), klass="context-link"))

        # DOI
        doi = self['doi']
        href = 'https://dx.doi.org/' + urllib.quote_plus(doi)
        row.append (TD (A(doi, href=href, target="doi"), klass="context-link"))

        # PUB_DATE
        row.append (TD (self['pub_date']))
        row.append (TD (self['created']))
        row.append (TD (self['lastmod']))

        return row


class DatasetTallyWriter (AwardIdDatasetReader):

    record_class = DatasetTallyRecord
    encoding = 'utf8'
    award_field = 'kuali_verified_award_ids'

    def __init__ (self, path, filter_args={}):
        AwardIdDatasetReader.__init__(self, path, filter_args)
        self.tally = self._get_tally()
        self.total_ids = self._get_total_ids()
        self.unique_ids = len (self.tally.keys())

    def get_rec(self, pid):
        return self.pid_map[pid ]

    def _get_tally (self):
        tally = {}
        for record in self.data:
            pid = record['pid']
            award_ids = filter (None, map (lambda x:x.strip(), record[self.award_field].split(',')))

            for award_id in award_ids:
                pid_list = tally.has_key(award_id) and tally[award_id] or []
                pid_list.append (pid)
                pid_list.sort()
                tally[award_id] = pid_list

        return tally

    def _get_total_ids (self):
        total = 0
        for key in self.tally.keys():
            total += len (self.tally[key])
        return total

    def get_tally_html(self):
        award_ids = filter (None, self.tally.keys())
        award_ids.sort(key = lambda x: -len(self.tally[x]))
        container = DIV(id="accordion")
        print len(award_ids), ' AWARD_IDS  '
        for award_id in award_ids:
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
            for field in ['pid', 'doi', 'pub_date', 'created', 'lastmod']:
                header_row.append (TH (field))
            table.append (header_row)
            for pid in pids:
                normalized_pid = pid.replace (':', '_');
                rec = self.get_rec(pid)
                row = rec.ashtml()
                row.update ({
                    'id' : normalized_pid,
                    'klass' : 'pub-row'
                })

                table.append(row)

            content.append(table)
        return container


class TallySliceWriter(SliceWriter):

    def __init__ (self, path, filter_args={}):
        self._data_table_html = None
        SliceWriter.__init__(self, path, filter_args)

    def get_dataset(self, path, filter_args):
        return DatasetTallyWriter(path, filter_args)

    def get_html_doc (self):
        """
        Generate the html document as string
        """
        # data_table = self.get_data_table_html()
        doc = SliceWriter.get_html_doc (self)
        doc.addJavascript ("../tally-script.js")
        doc.addStylesheet ("//code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css")
        doc.addStylesheet ("../tally-styles.css")
        doc.append (DIV ("This page was generated %s" % time.asctime(time.localtime()), id="page-date"))
        doc.append (DIV (id="debug"))
        doc.append (navbar.get_nav_bar('results-tally'))
        doc.append (H1 ('Award_ID Tally'))
        doc.append (H2 (self.title))

        num_records_total = len(self.dataset.data)
        num_unique_award_ids = len(self.dataset.get_unique_award_ids())

        all_records_stats = "{} Records, {} Unique Award_IDs".format(num_records_total, num_unique_award_ids)
        doc.append (DIV (all_records_stats, id="all-records-stats"))

        doc.append(self.dataset.get_tally_html())

        return doc

    def write_html(self):
        out_path = os.path.join(self.dirname, 'results-tally.html')
        fp = open(out_path,'w')
        fp.write (self.get_html_doc().__str__())
        fp.close()
        print 'wrote to ', out_path

if __name__ == '__main__':
    filter_args = {'start':'2020-01-01', 'end':'2020-08-01', 'date_field':'created'}
    sort_args = {'field':'created'}
    # csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/SMART_PARTIAL.csv'
    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/Award_Data_devel.csv'
    writer = TallySliceWriter (csv_path, filter_args)
    writer.write_html()