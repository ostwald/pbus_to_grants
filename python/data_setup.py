"""
from CSV (August_Testing/Last_5_yrs_DOI_Opensky_records.csv)
- create doi2pid json
- create DOI list

"""
import sys, os, json, re, time
from csv_reader import CsvReader

def write_doi_listing (csv_path, out_path):
    """
    we only want the UNIQUE dois
    :param csv_path:
    :param out_path:
    :return:
    """
    reader = CsvReader(csv_path)
    print '{} records'.format(len(reader.data))

    dois = set (filter (None, map (lambda rec:rec['doi'], reader.data)))

    fp = open(out_path, 'w')
    for doi in list(dois):
        fp.write(doi + '\n')
    fp.close()
    print 'wrote {} dois to {}'.format(len(dois), os.path.basename(out_path))

def write_doi2date_json(csv_path, out_path):
    reader = CsvReader(csv_path)
    print '{} records'.format(len(reader.data))
    json_data = {}
    in_fmt = '%m/%d/%y'
    out_fmt = '%Y-%m-%d'
    for rec in reader.data:
        pubdate = rec['pub_date']
        try:
            date_val = time.strftime(out_fmt    , time.strptime(pubdate, in_fmt))
        except:
            print "ERROR: in {} could not parse '{}': {}".format(rec['pid'], pubdate, sys.exc_info()[1])
            date_val = ''
        json_data[rec['doi']] = date_val
    fp = open(out_path, 'w')
    fp.write (json.dumps (json_data, indent=4))
    fp.close()
    print 'wrote {} mappings to {}'.format(len(reader.data), os.path.basename(out_path))

def write_doi2pid_json (csv_path, out_path):
    reader = CsvReader(csv_path)
    print '{} records'.format(len(reader.data))
    json_data = {}
    for rec in reader.data:
        json_data[rec['doi']] = rec['pid']
    fp = open(out_path, 'w')
    fp.write (json.dumps (json_data, indent=4))
    fp.close()
    print 'wrote {} mappings to {}'.format(len(reader.data), os.path.basename(out_path))

def write_pid2doi_json (csv_path, out_path):
    reader = CsvReader(csv_path)
    print '{} records'.format(len(reader.data))
    json_data = {}
    for rec in reader.data:
        json_data[rec['pid']] = rec['doi']
    fp = open(out_path, 'w')
    fp.write (json.dumps (json_data, indent=4))
    fp.close()
    print 'wrote {} mappings to {}'.format(len(reader.data), os.path.basename(out_path))

if __name__ == '__main__':

    # base_path = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/'
    # csv_path = os.path.join (base_path, 'Last_5_yrs_DOI_Opensky_records.csv')

    # base_path = '/Users/ostwald/devel/opensky/pubs_to_grants/award_id_data/'
    # csv_path = os.path.join (base_path, 'Award_id_data-Composite.csv')

    csv_path = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/DOI-REFERENCE_TABLE.csv'
    base_path = os.path.dirname(csv_path)
    if 1:
        out_path = os.path.join (base_path, 'OPENSKY_DOIS.txt')
        write_doi_listing (csv_path, out_path)

    if 1:
        out_path = os.path.join (base_path, 'doi2pid.json')
        write_doi2pid_json (csv_path, out_path)

    if 1:
        out_path = os.path.join (base_path, 'pid2doi.json')
        write_pid2doi_json (csv_path, out_path)

    if 1:
        out_path = os.path.join (base_path, 'doi2date.json')
        write_doi2date_json (csv_path, out_path)


