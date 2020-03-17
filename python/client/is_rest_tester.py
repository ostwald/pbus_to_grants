import sys, os, traceback, json, re

from ncarlibutils.fedora import CONFIG, get_datastream, update_datastream
from python.back_fill.notes_mods import NotesMODS

from ncarlibutils.dg import dg_api
from lxml import etree as ET
from ncarlibadmin.islandora_client import IslandoraObject


def remove_xml_dec (xml):
    # pat = re.compile ('\<\?xml*.\?\>')
    pat = re.compile ('\<\?xml.*\?\>[\s]*(.*)', re.DOTALL)
    m = pat.match (xml)
    if m:
        # print 'FOUND: "{}"'.format(m.group(1))
        # print 'FOUND: "{}"'.format(re.sub(pat, '', m.group()))
        print 'XML-DEC removed'
        return m.group(1)
    else:
        print 'NOT found'
    return xml


def update_mods_tester ():
    prod_pid = 'archives:8921'
    stage_pid = 'islandora:8'
    # stage_pid = 'articles:14475'

    obj = IslandoraObject(pid)


    MODS_stream = obj.get_mods_datastream()

    # print MODS_stream

    MODS_stream = remove_xml_dec (MODS_stream)

    #does MODS_stream have a xml-dec?

    mods = NotesMODS(MODS_stream, obj.pid)

    if 0:
        mods.add_funding_note ('fooberry')

    if 1:
        mods.remove_funding_notes ()


    mods_xml = ET.tostring(mods.dom)
    # mods_xml = None


    return obj.put_mods_datastream ({'label':label}, mods_xml)

    print 'RESPONSE ({})'.format(type(resp))
    print json.dumps(resp.json(), indent=3)



if __name__ == '__main__':
    print 80*'='
    print 'SERVICE_URL: {}'.format(CONFIG.get ("islandora_rest", "SERVICE_URL"))
    if 0:
        update_mods_tester()

