<?php
/**
 * Created by IntelliJ IDEA.
 * User: ostwald
 * Date: 2/21/19
 * Time: 11:17 AM
 *
 *  Given a DOI, retrieve award_ids from cross_ref and WOS, then filter them
 *  using Kuali API
 *
 *
 */

include 'utilities.inc';
include 'kuali.inc';

$BASE_DIR = '/Users/ostwald/devel/opensky/pubs_to_grants/ARTICLES_award_id_data/';
$KUALI_RESPONSE_CACHE = get_kuali_response_cache();

//$match_criterion = 'STRICT';
//$match_criterion = 'NAIVE_PARTIAL';
$match_criterion = 'SMART_PARTIAL';


function get_kuali_response_cache () {
    $kuali_cache_file = $GLOBALS['BASE_DIR'] .'kuali_cache.json';
    $cache = array();

    if (file_exists ($kuali_cache_file)) {
        $raw_cache = json_decode(file_get_contents($kuali_cache_file), true);
        foreach ($raw_cache as $key => $value) {
            $mykey = is_numeric($key) ? strval($key) : $key;
            $cache[$mykey] = $value;
    //        print '--> ' .  $mykey + "\n";
        }
    } else {
        print "cache file does not exist at $kuali_cache_file\n";
    }

    return $cache;
}

function write_get_kuali_response_cache() {
    $kuali_cache_file = fopen($GLOBALS['BASE_DIR'] .'/kuali_cache.json', "w");
    $cache_content = json_encode($GLOBALS['KUALI_RESPONSE_CACHE']);
    fwrite ($kuali_cache_file, $cache_content);
    fclose($kuali_cache_file);
//    echo "updated KUALI_RESPONSE_CACHE\n";
}

// ------------------------
/**
 * The vast majority of award_id values obtained from WOS and CrossRef are single grant numbers, but
 * sometimes award_id fields have extra stuff in them in addition to (or maybe instead of)
 * an actual award_id.
 *
 * Our approach is to
 * 1 - "tokenize" the award_id value by splitting it on spaces, then
 * 2 - keep only the tokens that might be award_ids (see get_award_id)

 *
 * @param $value - an award_id field obtained from WOS or CrossRef
 * @return array
 */
function get_award_id_tokens ($value)
{
    $values = array_filter(array_map('get_award_id', explode(" ", $value)));
//    print_r($values);
    return $values;
}

/**
 * Normalize the given $value by removing "special chars" and then, if the
 * result could be an award_id, return it. Otherwise return null.
 *
 * Possible award_ids must have at least 1 numeric char and must be longer than
 * 5 characters (the minimum that Kuali will match).
 *
 * @param $value -
 * @return mixed|null
 */
function get_award_id ($value) {

    $val = preg_replace("/[^A-Za-z0-9 ]/", '', $value);

    if (strlen($val) < 5) {
        return null;
    }

    // if it doesn't have a number, reject it
    preg_match("/[0-9]/", $val, $matches);

    return (sizeof($matches) < 1) ? null : $val;
}

/**
 * Given a list of award_fields obtained from WOS or CrossRef, tokenize the award_fields and
 * merge them all into a list of possible award_ids.
 *
 * @param $award_fields
 * @return array
 */
function tokenize_award_ids($award_fields) {

    $tokens = array();
    forEach ($award_fields as $raw_award_field) {
        $tokens = array_merge ($tokens, get_award_id_tokens($raw_award_field));
    }
    return $tokens;

}

function merge_award_ids ($wos_award_ids, $crossref_award_ids) {
    $merged_award_ids = array_unique(array_merge($crossref_award_ids, $wos_award_ids));
    // $merged_award_ids[] = 'FA9550-16-1-0050';  // one that we KNOW will validate just to test

    $tokenized_award_ids = tokenize_award_ids($merged_award_ids);
    $deduped_award_ids = dedup_award_ids($tokenized_award_ids);

    asort($deduped_award_ids);
    return $deduped_award_ids;
}

// ------------------------

/**
 * Remove items that are right-most substrings of another item in the given array
 *
 * @param $award_ids
 */
function dedup_award_ids ($award_ids) {
    $award_ids = array_unique($award_ids);
    $deduped = array();
    forEach ($award_ids as $candidate) {
        $is_right_subset = false;
        forEach ($award_ids as $id) {
            if ((strlen($id) > strlen($candidate)) && endswith($id, $candidate)) {
                $is_right_subset = true;
            }
        }
        if (!$is_right_subset) {
            $deduped[] = $candidate;
        }
    }
    return $deduped;
}


// ------------------------

function asTabDelimited($doi, $wos_ids, $crossref_ids, $validated_ids) {
    $pieces = array(
        implode(',', $wos_ids),
        implode(',', $crossref_ids),
        implode(',', $validated_ids),
    );
    return implode ("\t", $pieces);
}

function objAsTabDelimited($obj) {
//    $list_delimiter = chr(13);
    $list_delimiter = ',';
    $pieces = array(
        $obj['pid'],
        $obj['doi'],
        $obj['pub_date'],
        implode($list_delimiter, $obj['wos_award_ids']),
        implode($list_delimiter, $obj['crossref_award_ids']),
        implode($list_delimiter, $obj['validated_award_ids']),
    );
    return implode ("\t", $pieces);
}

function write_wos_response_OFF ($doi, $wos_dom) {
    $pid = doi2pid($doi);
    $path = $GLOBALS['BASE_DIR'] . 'metadata/wos/'. str_replace(':', '_', $pid) . '.xml';
    print "$path\n";
    file_put_contents($path, $wos_dom->saveXML());
}

function write_crossref_response_OFF ($doi, $crossref_dom) {
    $pid = doi2pid($doi);
    $path = $GLOBALS['BASE_DIR'] . 'metadata/crossref/'. str_replace(':', '_', $pid) . '.xml';
    print "$path\n";
    try {
        file_put_contents($path, $crossref_dom->saveXML());
    } catch (Exception $e) {
        echo 'Error: ' . $pid . ': ' . $e->getMessage();
    }
}

function get_header() {
    $pieces = array(
        'pid',
        'doi',
        'pub_date',
        'wos_award_ids',
        'crossref_award_ids',
        'validated_award_ids'
    );
    return implode ("\t", $pieces);
}

function test_doi($doi, $match_criterion) {

    $verbose = 0;
    $save_xml_responses = $GLOBALS['CACHE_XML_RESPONSES'];

    $crossref = get_crossref_dom($doi);

    $wos_xml = get_wos_dom($doi);
    $wos_data = opensky_get_wos_data($wos_xml);

    $wos_award_ids = $wos_data['award_ids'];

    if ($verbose) {
        print ("\nWOS Award Ids\n");
        print_r($wos_award_ids);
    }

    // get crossref award ids
    $crossref_award_ids = array();
    if (true) {
        // get award_ods from crossref
        $xpath = new DOMXpath($crossref);
        $selector = "//program/assertion/assertion[@name='award_number']";
        $nodes = $xpath->query($selector);

        if (is_null($nodes)) {
            print 'award_id not found in CROSSREF';
            return;
        } else {
            foreach ($nodes as $node) {
                $crossref_award_ids[] = $node->nodeValue;
            }
        }
    }

    if ($verbose) {
        print ("\nCrossRef Award Ids\n");
        print_r($crossref_award_ids);
    }

    $merged_award_ids = merge_award_ids($wos_award_ids, $crossref_award_ids);

    if ($verbose) {
        print ("\nMerged Award Ids\n");
        print_r($merged_award_ids);
    }

    $validated_award_ids = array();
    $num_cached_kuali_responses = count(array_keys($GLOBALS['KUALI_RESPONSE_CACHE']));
    foreach ($merged_award_ids as $award_id) {

        $award_id_key = is_numeric($award_id) ? (int)$award_id : $award_id;
        // test cache here
        if (isset ($GLOBALS['KUALI_RESPONSE_CACHE'][$award_id_key])) {
            $cached_award_id = $GLOBALS['KUALI_RESPONSE_CACHE'][$award_id_key];
            if ($cached_award_id) {
                $validated_award_ids[] = $cached_award_id;
                echo ("using CACHED Kuali repsonse for $award_id: $cached_award_id\n");
            }
        } else {
//            echo ("using realtime Kuali repsonse for $award_id\n");
            $resp = get_kuali_award_info($award_id, $match_criterion);


            // find the kuali version of the award_id to put in metadata
            if ($resp) {
                // print json_encode($resp, JSON_PRETTY_PRINT);
                // now pluck a value from the response. make sure the last
                // 5 chars match
                $fields_to_check = array ('sponsorAwardId', 'fainId');
                foreach ($fields_to_check as $field) {
                    $kuali_id = $resp[$field];
                    if (substr($kuali_id, -5) == substr($award_id, -5)) {
                        $validated_award_ids[] = $kuali_id;
                        $GLOBALS['KUALI_RESPONSE_CACHE'][strval($award_id_key)] = $kuali_id;
                        break;
                    }
                }
            }
            else {
                $GLOBALS['KUALI_RESPONSE_CACHE'][strval($award_id_key)] = false;
            }
        }
    }


    if (count(array_keys($GLOBALS['KUALI_RESPONSE_CACHE'])) > $num_cached_kuali_responses) {
        write_get_kuali_response_cache();
    }


    asort($validated_award_ids);
    if ($verbose) {
        print ("\nValidated Award Ids\n");
        print_r($validated_award_ids);
    }

    if ($verbose) {
        echo "returning\n";
        echo "pid: " . doi2pid($doi) . "\n";
        echo "doi: $doi\n";
        echo "pub_date: " . doi2date($doi) . "\n";
        echo "wos_award_ids: $wos_award_ids\n";
        echo "crossref_award_ids: $crossref_award_ids\n";
        echo "kuali_verified_award_ids: $validated_award_ids\n";
    }

    return array (
        'pid' => doi2pid($doi),
        'doi' => $doi,
        'pub_date' => doi2date($doi),
        'wos_award_ids' => $wos_award_ids,
        'crossref_award_ids' => $crossref_award_ids,
        'validated_award_ids' => $validated_award_ids,
    );
}

function process_multiple_dois($doi_blob, $match_criterion) {
    $dois = array_filter(array_map('trim', explode("\n", $doi_blob)));

    echo "there are " . count($dois) . " dois\n";
    $output_file = $GLOBALS['BASE_DIR'] . "$match_criterion.tsv";
    file_put_contents ($output_file, get_header() . "\n", FILE_APPEND);
    $max = 7000;
    $dois_cnt = count($dois);
    $cnt = 0;
    $start = 0;
    foreach ($dois as $doi) {
        if ($cnt < $start) {
            $cnt++;
            continue;
        }
        if ($cnt > $dois_cnt) {
            break;
        }

        try {
            $pid = doi2pid($doi);
        } catch (Exception $ex) {
            echo 'WARN: ' . $ex->getMessage() . "\n";
            continue;
        }
        $path = $GLOBALS['BASE_DIR'] . 'metadata/wos/'. str_replace(':', '_', $pid) . '.xml';

//        if (file_exists($path)) {
//            echo "- $pid exists\n";
//            continue;
//        }
       echo "pid: $pid,  doi: $doi\n";

        try {
            $result = test_doi($doi, $match_criterion);
        } catch (Exception $ex) {
            echo 'WARN: '. $doi . ' could not be processed: ' . $ex->getMessage() . "\n";
            continue;
        }
        $line = objAsTabDelimited($result) . "\n";
        file_put_contents ($output_file, $line, FILE_APPEND);
        sleep (0.2);
//         sleep(61);  // WOS Throttling!
        $cnt++;
        if ($cnt == $max) {
            break;
        }
        if ($cnt % 100 == 0) {
            echo "$cnt/$dois_cnt\n";
        }
    }
}

function test_single_pid ($pid, $match_criterion) {
    $doi = pid2doi($pid);
    echo "test_single_pid:  $pid\n";
    return test_single_doi($doi, $match_criterion);
}

function test_single_doi ($doi, $match_criterion)
{

    $ret = test_doi($doi, $match_criterion);
    //echo (asTabDelimited($doi, $wos_award_ids, $crossref_award_ids, $validated_award_ids));

    $record = objAsTabDelimited($ret);
    echo "\nRETurNED:\n";
    echo($record . "\n");
}


/*
 * Given a string containing DOIS separated by newlines, explode the string and call test_doi with each
 * Sleep after each call ...
 */
function test_process_multiple_dois ($match_criterion)
{
    $path = $GLOBALS['BASE_DIR'] . 'OPENSKY_DOIS.txt';
    $doi_blob = file_get_contents($path);
    echo ("got the blob\n");
//     echo ($doi_blob);
     process_multiple_dois($doi_blob, $match_criterion);
}

function array_tester ()
{
    $obj = array(
        'doi' => 'my_doi',
        'wos_award_ids' => array(),
        'crossref_award_ids' => array(),
        'validated_award_ids' => array('some_id'),
    );

    $output_file = "/Users/ostwald/tmp/DOI_KUALI_TESTING.txt";

    $line = objAsTabDelimited($obj) . "\n";
    file_put_contents($output_file, $line, FILE_APPEND);
}


test_process_multiple_dois($match_criterion);

if (0) {
    // DOI passed as command line argument, e.g. 10.1038/s41597-020-0534-3
    // % php doi_tester.php
    if (count($argv) > 1) {
//        test_single_doi($argv[1], $match_criterion);
        $crossref = get_crossref_dom($argv[1]);
        print ("CrossRef for $doi\n");
        print ($crossref->saveXML());
        $dest = '/Users/ostwald/tmp/CROSSREF-DOC.xml';
        file_put_contents($dest, $crossref->saveXML());
        print ("Wrote to $dest\n");
    } else {
        print "A DOI is required\n";
    }
}

if (FALSE) {
    // DOI passed as command line argument, e.g. 10.1038/s41597-020-0534-3
    // % php doi_tester.php
    if (count($argv) > 1) {
        test_single_doi($argv[1], $match_criterion);
    } else {
        print "A DOI is required\n";
    }
}

if (0) {  // KUALI RESP CACHE testing

    if (count($argv) > 1) {
        test_single_pid($argv[1], $match_criterion);
    } else {
        print "A PID is required\n";
    }
}