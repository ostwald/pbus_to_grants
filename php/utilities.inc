<?php

/**
 * @file
 * Utility functions.
 */

$READ_FROM_DISK = 0;

//$BASE_DIR = '/Users/ostwald/devel/opensky/pubs_to_grants/DOI-based_Testing/';
//$BASE_DIR = '/Users/ostwald/devel/opensky/pubs_to_grants/August_Testing/';
$BASE_DIR = '/Users/ostwald/devel/opensky/pubs_to_grants/2020_02_20_Testing/';


function doi2pid ($doi) {
    if (!isset($GLOBALS['doi2pid_map'])) {
        $contents = file_get_contents ($GLOBALS['BASE_DIR'] . 'doi2pid.json');
        $GLOBALS['doi2pid_map'] = json_decode($contents, true);
    }
    if (!isset($GLOBALS['doi2pid_map'][$doi])) {
        throw new Exception ("doi not found: $doi");
    }
    return $GLOBALS['doi2pid_map'][$doi];
}


function doi2date ($doi) {
    if (!isset($GLOBALS['doi2date_map'])) {
        $contents = file_get_contents ($GLOBALS['BASE_DIR'] . 'doi2date.json');
        $GLOBALS['doi2date_map'] = json_decode($contents, true);
    }
    if (!isset($GLOBALS['doi2date_map'][$doi])) {
        throw new Exception ("doi not found: $doi");
    }
    return $GLOBALS['doi2date_map'][$doi];
}

function get_wos_from_disk ($doi) {
    return get_source_from_disk ($doi, 'wos');
}

function get_crossref_from_disk ($doi) {
    return get_source_from_disk ($doi, 'crossref');
}

function get_source_from_disk ($doi, $source) {
    $pid = doi2pid($doi);
    $base = $GLOBALS['BASE_DIR'] . "$source/";
    $path = $base . str_replace(':', '_', $pid) . '.xml';
//    print "got $path from disk\n";
    return file_get_contents($path);
}

/*
 * Returns DOMDocument
 */
function get_crossref_dom ($doi) {
    $crossref_xml = new DOMDocument('1.0');
    if ($doi) {
        if ($GLOBALS['READ_FROM_DISK']) {
            $crossref_xml_source = get_crossref_from_disk($doi);
        } else {
            $crossref_xml_source = islandora_doi_perform_request_stand_alone($doi);
        }
        if (!$crossref_xml->loadXML($crossref_xml_source)) {
            print "CROSS REF LOAD XML FAILED\n";
            return FALSE;
        }
    } else {
         // read xml from file into DOMDocument

        $crossref_xml_source = '/Users/ostwald/devel/opensky/pubs_to_grants/xml/crossref-sample.xml';
        if (!$crossref_xml->load($crossref_xml_source)) {
            print "CROSS REF FAILED\n";
            return FALSE;
        }
    }
    return $crossref_xml;
}

/*
 * Returns DOMDocument
 */
function get_wos_dom ($doi) {
    $doi = null; // force to use canned
    if ($doi) {
        if ($GLOBALS['READ_FROM_DISK']) {
            $wos_xml_source = get_wos_from_disk($doi);
        } else {
            $wos_xml_source = opensky_doi_get_wos_response($doi);
        }
    } else {
        $wos_xml_source = get_canned_wos_response($doi);
    }

//    var_dump ($wos_xml_source);


    $wos_xml = new DOMDocument('1.0');
    if (!$wos_xml_source) {
        print ("Did not get WOS xml for $doi\n");
    }
    else if (!$wos_xml->loadXML($wos_xml_source)) {
        print "WOS load FAILED\n";
        return $wos_xml;
    }

    return $wos_xml;
}

/*
 * Return XML String
 * DOI not used for this canned version ....
 */
function get_canned_wos_response ($doi) {
//    $path = '/Users/ostwald/tmp/WOS_DATA.xml';
    $path = '/Users/ostwald/devel/opensky/pubs_to_grants/xml/wos_data.xml';
    $wos_data_str = file_get_contents($path);
    return $wos_data_str;
}

/**
 *  * Get WOS response for the given DOI.
 *
 * @param string $id
 *   A DOI.
 *
 * @return XML String containing abstract and funderInfo
 */

function opensky_doi_get_wos_response($id) {
//    print 'getting WOS DATA from web ..';
    $auth_url = "http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl";

    try {
        // see http://php.net/manual/en/class.soapclient.php
        $opts = array(
            'ssl' => array(
                'verify_peer'=>false,
                'verify_peer_name'=>false
            )
        );
        // SOAP 1.2 client
        $params = array (
            'login' => "NCAR",
            'password' => "OLCP2YXI",
            'stream_context' => stream_context_create($opts)
        );

        $auth_client = new SoapClient ( $auth_url, $params );

    } catch (Exception $e) {
        error_log ('ERROR: ' . $e->getErrorMessage());
    }

    $auth_response = @$auth_client->authenticate();

    if (!$auth_response) {
        throw new Exception ("Could not authenticate NCAR client for WOS");
    }

    $search_url = "http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl";
    $search_client = @new SoapClient($search_url);
    $search_client->__setCookie('SID', $auth_response->return);
    $id = '"' . $id . '"';

    $search_array = array(
        'queryParameters' => array(
            'databaseId' => 'WOS',
            'userQuery' => 'DO=' . $id,
            'editions' => array(
                array('collection' => 'WOS', 'edition' => 'SCI')
            ),
            'queryLanguage' => 'en'
        ),
        'retrieveParameters' => array(
            'count' => '5',
            'fields' => array(
                array('name' => 'Date', 'sort' => 'D')
            ),
            'firstRecord' => '1',
//            'viewField' => array('collectionName' => 'WOS', 'fieldName' => 'abstract')
            'viewField' => array('collectionName' => 'WOS', 'fieldName' => array ('abstract', 'grants'))
        )
    );

    try {
        $search_response = $search_client->search($search_array);
        if ($search_response->return->recordsFound > 0) {
            $returnedxml = simplexml_load_string($search_response->return->records);
            $returnedxml_str =  $returnedxml->asXML();
        } else {
            $returnedxml_str = NULL;
        }
    } catch (Exception $e) {
        echo $e->getMessage();
        $abstract = "Error";
    }
    return $returnedxml_str;  // return xml string
}


/*
 * Extract information obtained from WOS webservice response
 * provided $wos_xml is an XML string
 * - abstract text
 * - award_ids as array
 */
function opensky_get_wos_data ($wos_xml) {

    $abstract = null;
    $xpath = new DOMXpath($wos_xml);
    $xpath->registerNamespace("ns", $wos_xml->documentElement->namespaceURI);
    $nodes = $xpath->query("//ns:abstract_text/ns:p");


    if (is_null($nodes)) {
        print 'Abstract not found in WOS_XML';
    } else {
        $wos_abstract_node = $nodes->item(0);

        if ($wos_abstract_node) {
            $abstract = $wos_abstract_node->nodeValue;
        }
    }


    $award_ids = array();
    $xpath = new DOMXpath($wos_xml);
    $xpath->registerNamespace("ns", $wos_xml->documentElement->namespaceURI);
    $id_nodes = $xpath->query("//ns:fund_ack/ns:grants/ns:grant/ns:grant_ids/ns:grant_id");

    // NOTE: there can be dupe grant_agency names in the data!

    foreach ($id_nodes as $node) {
        $award_ids[] = $node->nodeValue;
    }
    return array (
        'award_ids' => $award_ids,
        'abstract' => $abstract,
    );
}



function islandora_doi_perform_request_stand_alone($id_or_url) {
//    print 'getting CROSSREF DATA from web ..';

    // Allows for $id to pass a DOI url string or the DOI name.
    $id = islandora_doi_get_doi_name_from_url($id_or_url);

    $openurl = "http://www.crossref.org/openurl";
    $openurl_pid = "opensky@ucar.edu";

    $params = array(
        'noredirect' => 'true',
        'pid' => $openurl_pid,
        'format' => 'unixref',
        'id' => ((strpos($id, 'doi:') === 0) ? $id : 'doi:' . $id),
    );

    $query_str = http_build_query($params);

    $url = $openurl . '?' . $query_str;
    return file_get_contents($url) ."\n";
}


/**
 * Get the DOI name for the given url.
 *
 * @param string $doi_url
 *   A DOI url, or a DOI name with or without the "doi:" prefix. If the $url
 *   is a CrossRef ID passed in as doi:10.1016/j.tiv.2011.10.017 or
 *   10.1111/eve.12339 it will not get changed by running it through parse_url.
 *
 * @return string
 *   A string containing the DOI name.
 */
function islandora_doi_get_doi_name_from_url($doi_url) {
  // Allows for DOI to be entered in the following formats: 10.1111/eva.12339,
  // http://dx.doi.org/10.1111/eva.12339, http://doi.org/10.1111/eva.12339,
  // or doi:10.1111/eva.12339. Removing whitespace before parsing the url and
  // then removing any trailing "/" from the returned path.
  $doi_name = trim(parse_url(trim($doi_url), PHP_URL_PATH), '/');
  return $doi_name;
}


