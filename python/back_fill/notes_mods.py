import re, sys
from UserList import UserList
from lxml import etree as ET

sys.path.append ('/Users/ostwald/devel/projects/library-utils')
sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibutils.fedora import CONFIG, get_datastream, update_datastream
from ncarlibadmin.model.mods import MODS

sys.path.append ('/Users/ostwald/devel/opensky/pubs_to_grants')
from python.client import KualiClient

class AbstractFunderNote:

    old_funder_pat = re.compile('.*?:[\s]+([\S]*)')  #  abbrev ignored
    award_id_pat = re.compile('[^a-zA-Z0-9]') # used to get rid of all but letters and numbers

    def __init__ (self):
        self.original = None
        self.award_id = None
        self.kuali_id = None
        self.is_legacy = None

    def get_award_id (self):
        m = self.old_funder_pat.match(self.original)
        if m:
            # return m.group(1)
            return self.award_id_pat.sub('', m.group(1))

        else:
            return self.original

    def get_kuali_id (self):
        client = KualiClient()
        return client.get_kuali_award_id(self.award_id) or None

    def get_is_legacy (self):
        """
        :return: True if note_el has displayLabel="Legacy funding data"
        """
        m = self.old_funder_pat.match(self.original)
        if m:
            return True
        else:
            return False

    def __repr__ (self):
        s = self.original
        s += '\n- award_id: {}'.format(self.award_id)
        s += '\n- kuali_id: {}'.format(self.kuali_id)
        s += '\n- is_legacy: {}'.format(self.is_legacy)
        return s

class FunderNote(AbstractFunderNote):

    def __init__ (self, note_el):
        self.note_el = note_el
        self.original = self.note_el.text
        self.award_id = self.get_award_id()
        self.kuali_id = self.get_kuali_id()
        self.is_legacy = self.get_is_legacy()

    def has_legacy_markup (self):
        """
        :return: True if note_el has displayLabel="Legacy funding data"
        """
        # print 'LOOKING'
        # if self.note_el.get ('displayLabel'):
        #     print 'found attr'
        #     return self.note_el.get('displayLabel') == 'Legacy funding data'
        # else:
        #     print '... NOT found'
        return self.note_el.get('displayLabel') == 'Legacy funding data'

    def __repr__ (self):
        s = AbstractFunderNote.__repr__(self)
        s += '\n- has_legacy_markup: {}'.format(self.has_legacy_markup())
        return s

class MockFunderNote (AbstractFunderNote):

    def __init__ (self, award_id):
        self.original = award_id
        self.award_id = self.get_award_id()
        self.kuali_id = self.get_kuali_id()
        self.is_legacy = None

class AwardIdList (UserList):
    """
    stores award_ids and whether items are legacy

    creates funding xml based on contents
    """

    def add_item (self, award_id, legacy=False):
        self.append ([award_id, legacy])

    def __repr__ (self):
        s = "\nAward_IDs"
        for item in self:
            s += '\n- {}'.format(item[0])
            if item[1] == True:
                s += " Legacy"
        return s


class NotesMODS (MODS):
    """
    Extends MODS by providing support for the Notes element, particularly for FUNDING notes

    e.g., a 'note' element used for associating funding with this record
    """
    dowrites=0
    debugging=0
    old_funder_pat = re.compile('.*?:[\s]+([\S]*)')  #  abbrev ignored

    def __init__ (self, data, pid):
        self.pid = pid
        self.xpaths['note'] = '/mods:mods/mods:note[@type="funding"]'
        self.xpaths['corporate_funder'] = "/mods:mods/mods:name[@type='corporate']/mods:role/mods:roleTerm"
        MODS.__init__ (self, data)
        if self.dom is None:
            print "NotesMODS WARN: DOM not found"

    def extract_award_id (self, element):
        content = element.text
        m = self.old_funder_pat.match(content)
        if m:
            return m.group(1)
        else:
            return content

    def get_corporate_funders (self):

        # funders = self.selectNodesAtPath (self.xpaths['corporate_funder'])
        # funders = self.names

        funders = filter (lambda x:x.type=='corporate' and x.role=='funder', self.names)

        return funders


    def get_funding_notes (self, filter_spec=None):
        """
        :return: a list of all 'note' elements
        """
        notes = self.selectNodesAtPath (self.xpaths['note'])
        if filter_spec == 'verified_only':
            return filter (lambda x:x.get('displayLabel') is None, notes)
        if filter_spec == 'legacy_only':
            return filter (lambda x:x.get('displayLabel') is not None, notes)
        return notes
    
    def remove_funding_notes(self):
        """
        remove each of the notes in the DOM (as obtained by get_funding_notes(())
        """
        for note_el in self.get_funding_notes():
            note_el.getparent().remove(note_el)

    def remove_funding_note(self, award_id, is_legacy=False):
        for note_el in self.get_funding_notes():
            if note_el.text.strip() == award_id:
                if is_legacy and note_el.attrib['displayLabel'] == 'Legacy funding data':

                    note_el.getparent().remove(note_el)
                elif not is_legacy:
                    note_el.getparent().remove(note_el)

    def add_funding_note (self, award_id, is_legacy=False):
        """
        add a note[@type='funding'] element to the DOM
        :param award_id: kuali record handle
        :param is_legacy: true if award_id cannot be verified in Kuali
        :return:
        """
        NS = "{%s}" % self.namespaces['mods']
        note = ET.SubElement(self.dom, NS+'note')
        note.attrib['type'] = 'funding'
        if is_legacy:
            note.attrib['displayLabel'] = 'Legacy funding data'
        note.text = award_id

    def remove_corporate_funders(self):
        funders = self.get_corporate_funders()
        # print '{} coporate funders to remove'.format(len (funders))

        for funder in funders:
            element = funder.element
            # print ET.tostring(element)
            element.getparent().remove(element)

    def get_funder_map (self, items, field):
        my_map = {}
        for item in items:
            key = getattr(item, field)
            if key is None:
                continue
            values = my_map.has_key(key) and my_map[key] or []
            values.append (item)
            my_map[key] = values
        return my_map

    def do_back_fill (self, ids_to_add=None):
        """
        insert new award_ids into this Record


        - we only want to insert Kuali-API versions of IDS, and
         - we don't want any dups, AND
         - we want to mark IDS that cannot be found in Kuali as "Legacy"
        """

        if ids_to_add is None:
            ids_to_add = []

        TO_ADD = map (MockFunderNote, ids_to_add)

        if self.debugging:
            funders = self.get_corporate_funders()
            print 'Corporate funders BEFORE removal'
            for f in funders:
                print 'type - {}, {}'.format (f.type, f.role)

        #  Remove the old-style corporate_name element for the funder
        self.remove_corporate_funders()

        if self.debugging:
            funders = self.get_corporate_funders()
            print 'Corporate funders AFTER removal ({})'.format(len(funders))
            for f in funders:
                print 'type - {}, {}'.format (f.type, f.role)

        note_elements = self.get_funding_notes()

        NOTES = map (FunderNote, note_elements)

        if 0 or self.debugging:
            print '\n{} To ADD'.format(len(TO_ADD))
            for note in TO_ADD:
                print note

            print '\n{} NOTES '.format(len(NOTES))
            for note in NOTES:
                print note

        # find and delete dup kuali_ids
        all_notes = TO_ADD + NOTES
        keepers = AwardIdList()
        
        if self.debugging:
            print u'\n{} All NOTES '.format(len(all_notes))
            for note in all_notes:
                print unicode(note)

        kuali_id_map = self.get_funder_map(all_notes, 'kuali_id')
        for kuali_id in kuali_id_map.keys():
            items = kuali_id_map[kuali_id]
            for i, item in enumerate (items):
                if i == 0:
                    keepers.add_item (kuali_id)
                all_notes.remove (item)

        award_id_map = self.get_funder_map(all_notes, 'award_id')
        for award_id in award_id_map.keys():
            items = award_id_map[award_id]
            # sort by longest original first
            items.sort (key=lambda x:-len(x.original))
            for i, item in enumerate (items):
                # print '  {} - {}'.format(i, item)
                if i == 0:
                    keepers.add_item (item.original, True)
                all_notes.remove (item)

        for item in all_notes:
            keepers.add_item (item.original, True)

        print '\n{} KEEPERS'.format(self.pid)
        for k in keepers:
            print k


        # print '\nRemoving {} notes'.format(len(note_elements))
        for note in note_elements:
            note.getparent().remove(note)

        for item in keepers:
            self.add_funding_note(item[0], item[1])

        # print '+'*50
        # sys.exit()



        if self.dowrites:
            update_datastream (self.pid, 'MODS', self.dom)
            print ' - {} was updated'.format(self.pid)
        else:
            print ' - {} woulda been updated'.format(self.pid)

    def do_back_fill_first_pass (self, ids_to_add):
        """
        insert new award_ids into this Record


        - we only want to insert Kuali-API versions of IDS, and
         - we don't want any dups, AND
         - we want to mark IDS that cannot be found in Kuali as "Legacy"
        """

        if ids_to_add is None:
            ids_to_add = []

        if self.debugging:
            funders = self.get_corporate_funders()
            print 'Corporate funders BEFORE removal'
            for f in funders:
                print 'type - {}, {}'.format (f.type, f.role)

        #  Remove the old-style corporate_name element for the funder
        self.remove_corporate_funders()

        if self.debugging:
            funders = self.get_corporate_funders()
            print 'Corporate funders AFTER removal ({})'.format(len(funders))
            for f in funders:
                print 'type - {}, {}'.format (f.type, f.role)

        note_elements = self.get_funding_notes()

        if self.debugging:
            print ' - {} note_elements found'.format(len(note_elements))

            print ' - {} award_ids to insert\n'.format(len(ids_to_add))

            if self.debugging:
                print 'BEFORE inserting award_ids'
                self.show_notes()


        if 1: # PROCESS EXISTING FUNDING NOTES
            client = KualiClient()
            for note_el in note_elements:

                award_id = self.extract_award_id(note_el)
                kuali_id = client.get_kuali_award_id(award_id) or None

                print '\norginal {}'.format(note_el.text)
                print ' - award_id: {} kuali_id: {}'.format(award_id,kuali_id)

                if kuali_id is None:
                    note_el.attrib['displayLabel'] = 'Legacy funding data'
                    # note_el.text = award_id

                else:
                    # print '\nKuali award_id found: {}'.format(kuali_id)

                    if kuali_id in ids_to_add:
                        print ' - {} collision'.format(kuali_id)
                        # delete this id from ids_to_add
                        ids_to_add.remove (kuali_id)

                    note_el.text = kuali_id
                    if note_el.attrib.has_key('displayLabel'):
                        del (note_el.attrib['displayLabel'])


        if 1: # insert new funding notes
            for id in ids_to_add:
                NS = "{%s}" % self.namespaces['mods']
                note = ET.SubElement(self.dom, NS+'note')
                note.attrib['type'] = 'funding'
                note.text = id

        if self.debugging:
            print 'AFTER inserting funding notes'
            self.show_notes()


        if self.dowrites:
            update_datastream (self.pid, 'MODS', self.dom)
            print ' - {} was updated'.format(self.pid)
        else:
            print ' - {} woulda been updated'.format(self.pid)


    def show_notes (self):
        note_elements = self.get_funding_notes()
        print '{} note_elements'.format(len(note_elements))
        for note in note_elements:
            # print ET.tostring(note)
            displayLabel = None
            if note.attrib.has_key('displayLabel'):
                displayLabel = note.attrib['displayLabel']
            s = note.text
            if displayLabel is not None:
                s += ' - displayLabel="{}"'.format(displayLabel)
            print ' - ', s

def backfilltest (pid, ids):
    """
    insert the award_id into the object's MODS stream

    """
    if 1:
        # fedoraObj = FedoraObject (pid)
        # mods_xml = fedoraObj.get_datastream('MODS')
        mods_xml = get_datastream (pid, 'MODS')
    else:
        path = '/Users/ostwald/Downloads/archives-8918-updated.xml'
        mods_xml = open(path, 'r').read()
    NotesMODS.dowrites = 0
    mods = NotesMODS(mods_xml, 'archives:8918')

    print 'BEFORE Backfill'
    mods.show_notes()

    mods.do_back_fill(ids)

    print 'AFTER Backfill'
    mods.show_notes()
    # print mods




if __name__ == '__main__':
    if 0:
        pid = 'articles:20981' # has dups
        # pid = 'articles:22793' # has legacy

        # award_ids = [] # ['fee', 'foo']
        # award_ids = [ '55088'] # collision tester
        # award_ids = None
        award_ids = ['1211668',]
        backfilltest (pid, award_ids)

    if 1:
        pid = 'islandora:15'
        # pid = 'archives:8922'
        mods_xml = get_datastream (pid, 'MODS')

        mods = NotesMODS(mods_xml, pid)

        id = '4567'
        NS = "{%s}" % mods.namespaces['mods']
        note = ET.SubElement(mods.dom, NS+'note')
        note.attrib['type'] = 'funding'
        note.text = id

        print mods


        # res = update_datastream (pid, 'MODS', mods.dom)
        print res