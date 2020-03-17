import os, sys, traceback


sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')

from ncarlibadmin.model.fedora import FedoraObject
from ncarlibutils.fedora import CONFIG, get_datastream, update_datastream

from UserDict import UserDict
sys.path.append ('/Users/ostwald/devel/opensky/pubs_to_grants/python')
from csv_processor import CsvReader, CsvRecord
from notes_mods import NotesMODS

class SafeDict (UserDict):

    def __getitem__(self, item):
        try:
            return self.data[item]
        except:
            return None

class BackFillRecord (CsvRecord):

    verbose = 1

    def __init__ (self, data, schema):
        CsvRecord.__init__ (self, data, schema)

        self.award_ids = self.get_award_ids()
        self._mods = None

    def get_mods_instance(self):
        if self._mods is None:
            mods_xml = get_datastream(self['pid'], 'MODS')
            self._mods = NotesMODS(mods_xml, self['pid'])
        return self._mods

    def get_award_ids(self):
        ids = self['award_ids'].split(',')
        ids = map (lambda x:x.strip(), ids)
        ids = filter (lambda x: len(x)>0, ids)
        return ids

    def backfill (self):
        """
        its actually NotesMODS that does the back fill
        here we set it up and then call NotesMODS.do_back_fill
        """
        mods = self.get_mods_instance()
        # if self.verbose:
        #     print 'BEFORE'
        #     mods.show_notes()
        try:
            mods.do_back_fill(self.award_ids)
            # print mods
            # print 'AFTER'
            # mods.show_notes()
        except:
            print 'ERROR: {}'.format(sys.exc_info()[1])
            traceback.print_exc()



class BackFiller (CsvReader):
    """
    read in a table of backfill data
    records have form of:
    pid, doi, kuali_award_ids

    """
    record_class = BackFillRecord
    dowrites = 0

    def __init__ (self, path):
        CsvReader.__init__ (self,path)
        self._pid_map = None

    def get_pid_map(self):
        if self._pid_map == None:
            self._pid_map = SafeDict()
            for rec in self.data:
                self._pid_map[rec['pid']] = rec
        return self._pid_map

    def get_record(self, pid):
        return self.get_pid_map()[pid]

    def back_fill (self):
        NotesMODS.dowrites = self.dowrites
        print 'BACK_FILL - dowrites is {}'.format(NotesMODS.dowrites)
        for rec in self.data:

            pid = rec['pid']
            award_ids = rec.award_ids

            if len(award_ids) > 0:
                print '{} ({})'.format(pid, len(award_ids))
                # mods = get_mods(pid) #???

                fedoraObj = FedoraObject (pid)
                # mods = fedoraObj.get_MODS_instance
                mods_xml = fedoraObj.get__MODS_stream()

                for award_id in award_ids:
                    print ' - {}'.format(award_id)

                mods_rec = NotesMODS(mods_xml, pid)
                mods_rec.do_back_fill (award_ids)

        print '\nBackfill completed'


    def backup_mods(self):
        backup_dir = '/Users/ostwald/tmp/BACKUP_MODS'
        if not os.path.exists(backup_dir):
            os.mkdir (backup_dir)
        for rec in self.data:
            pid = rec['pid']
            fedoraObj = FedoraObject (pid)
            mods_xml = fedoraObj.get__MODS_stream()
            fp = open (os.path.join (backup_dir, pid.replace(':','_') + '.xml'), 'w')
            fp.write (mods_xml.encode('UTF8'))
            fp.close()
        print 'done backing up to {}'.format(backup_dir)


    def writeTabDelimited (self, path='BACKFILLER_TABDELIMITED.txt'):
        """
        write only records that have a Kuali-vetted award_id
        :param path:
        :return:
        """
        lines = [];add=lines.append
        header = ['pid','doi','award_ids']
        add (header)
        for rec in self.data:
            if len (rec.award_ids) > 0:
                add ([rec['pid'], rec['doi'], ','.join (rec.award_ids)])
        # fp = codecs.open (path, 'w')
        fp = open (path, 'w')
        fp.write ('\n'.join (map (lambda x:'\t'.join(x), lines)))
        fp.close()
        # print '{} records written to {}'.format(len(self.data), path)
        print 'Data written to {}'.format(path)

def back_fill_pid_tester (pid):
    if 0: ## get award_ids from Kuali
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/KUALI_FILTERED_TRIAL_RECS.csv'
        backfiller = BackFiller(csv_path)

        rec = backfiller.get_record(pid)
        print '\n{}'.format(rec['pid'])
        award_ids = rec.award_ids
    else:
        award_ids = [
            # 'National Science Foundation (NSF): 3459948',
            # '3459948',
            # 'whatever: 3-45-9948',
            # '34984'
        ]
    fedoraObj = FedoraObject (pid)
    mods_xml = fedoraObj.get__MODS_stream()
    NotesMODS.dowrites = 1
    rec = NotesMODS (mods_xml, pid)
    rec.do_back_fill(award_ids)
    return rec


if __name__ == '__main__':
    pid = 'articles:17024'
    # pid = 'articles:22261' # has old-style data
    # pid = 'articles:21956' # has old-style data

    rec = back_fill_pid_tester (pid)
    # print rec