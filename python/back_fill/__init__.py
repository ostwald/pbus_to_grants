"""
use the cvs reader to fetch the info needed to write Kuali-approved award_ids to OpenSky records

- NOTE: we will rely on library-utils, so this code can be run in a virtualenv ...

first, lets just assume an award_id and write it to a given pid.


"""
import os, sys, re, codecs, traceback

sys.path.append ('/Users/ostwald/devel/projects/library-utils')
from ncarlibutils.fedora import CONFIG, get_datastream, update_datastream



sys.path.append ('/Users/ostwald/devel/projects/library-admin')
from ncarlibadmin.model.fedora import FedoraObject
from ncarlibadmin.model.mods import MODS
from ncarlibadmin.batch import feed as feeds

from back_filler import BackFiller
from notes_mods import NotesMODS
from lxml import etree as ET




def get_mods(pid):
    ds = get_datastream(pid, 'MODS')
    return ds

def update_old_funder_records():
    """
    The Kuali backfill updated the records that also had Kuali IDs, but there are
    452 that still have old-school funder info (mods_name_corporate_funder_s:*).

    <name type="corporate">
        <namePart>National Science Foundation (NSF)</namePart>
        <role>
            <roleTerm type="text" authority="marcrelator">funder</roleTerm>
        </role>
    </name>
    <note type="funding">National Science Foundation (NSF): 1852977</note>

    Now we want to remove the corporate funder info, and try to normalize the
    award_ids with Kuali-verfied versions. If ids can't be normlized thus, then
    add a 'displayLabel' = 'Legacy funding data'  attribute

    """
    dowrites = 0

    args = {
        'params' :
            {
                'q': 'mods_name_corporate_funder_s:*'
            },
        'baseUrl': CONFIG.get("fedora", "SERVER") + CONFIG.get("fedora", "SOLR_PATH"),
    }
    feed = feeds.SolrSearchFeed(**args)
    print 'feed has {}'.format(len(feed.pids))
    NotesMODS.dowrites = dowrites

    for pid in feed.pids:
        print pid
        mods_xml = get_datastream (pid, 'MODS')
        mods = NotesMODS(mods_xml, pid)

        # print 'BEFORE Backfill'
        # mods.show_notes()
        mods.do_back_fill([])
        # print mods

def update_mods_from_file (pid, path):
    from lxml import etree as ET

    mods_doc = ET.parse (path)

    try:
        update_datastream(pid, 'MODS', mods_doc)
        print ET.tostring (mods_doc, pretty_print=1)
    except:
        print traceback.print_exc()


if __name__ == '__main__':

    print 50*'='
    print 'Fedora server:', CONFIG.get("fedora", "SERVER")

    if 1:
        pid = 'islandora:15'
        path = '/Users/ostwald/Downloads/islandora_15.xml'
        update_mods_from_file (pid, path)

    if 0: #Prepare CSV for back_filling
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/back_fill_data.csv'
        filler = BackFiller(csv_path)
        # filler.back_fill()
        filler.writeTabDelimited('/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/KUALI_FILTERED_TRIAL_RECS.txt')


    if 0:  # perform Backfill
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/KUALI_FILTERED_TRIAL_RECS.csv'
        backfiller = BackFiller(csv_path)
        backfiller.dowrites = 1
        backfiller.back_fill()

    if 0:  # perform Backfill
        csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/back_fill/KUALI_FILTERED_TRIAL_RECS.csv'
        backfiller = BackFiller(csv_path)
        backfiller.backup_mods()

    if 0:
        pid = 'archives:8918'
        print get_mods(pid)

    if 0:
        update_old_funder_records()