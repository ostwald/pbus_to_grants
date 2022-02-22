<?php

include 'kuali.inc';

function full_test_award_id ($award_id)
{
    print "------------------\n$award_id\n";
    if (1) {
        $response = get_kuali_response($award_id);
        print ("\nRESPONSE\n");
        print_r($response);
    }

    if (1) {
        $match_criteria = array(
            'NAIVE_PARTIAL',
            'SMART_PARTIAL',
            'STRICT',
        );
        foreach ($match_criteria as $match_criterion) {
            $info = get_kuali_award_info($award_id, $match_criterion);
            print "\nResult - $match_criterion\n";
            if ($info == null) {
                print "NULL\n";
            } else {
                print_r($info);
            }
        }
    }
}

function test_award_id ($award_id) {
//    $response = get_kuali_response($award_id);
    $response = get_kuali_award_info($award_id);
    print json_encode($response, JSON_PRETTY_PRINT)."\n";
}

function test_awards_ids($award_ids) {
    foreach ($award_ids as $award_id) {
        // test_award_id ($award_id);
//        print "\nTEST AWARD_ID \"$award_id\" --------------------------\n";
        $kuali_award_id = get_kuali_award_id ($award_id);
        if ($kuali_award_id) {
//            print "Kuali award_id: $kuali_award_id\n";
            print "$award_id\t$kuali_award_id\n";
        }
        else {
//            print "Kuali award_id: not found\n";
        }
    }
}

function find_unique_candidates ($award_id) {
    $response = get_kuali_response($award_id);

    if (!isset ($response[0])) {
        // this is an object, which means an empty result
        print "no results found\n";
        return null;
    }

    $fields_to_check = array ('sponsorAwardId', 'fainId');
    $sought_award_id = sanitize_id ($award_id);
    $unique_kuali_ids = array();
    print count($response) . " results\n";
    foreach ($response as $result) {
        print_r($result);
        foreach($fields_to_check as $field) {
            $kuali_award_id = sanitize_id($result[$field]);
            if (endsWith($kuali_award_id, $sought_award_id) ||
                endsWith($sought_award_id, $kuali_award_id)) {
                print "$award_id - partial match with $field field\n";
                $unique_kuali_ids[] = $kuali_award_id;
            }
        }
    }
    foreach (array_unique($unique_kuali_ids) as $id) {
        print "$id\n";
    }
}

function get_ids_from_file ($path) {
    $id_blob = file_get_contents($path);
    $ids = array_filter(array_map('trim', explode("\n", $id_blob)));
    return $ids;
}

if (count($argv) > 1) {
//    full_test_award_id($argv[1]);
    // test_award_id($argv[1]);
    find_unique_candidates($argv[1]);
}

if (0) {
    $ids = array(
//    'FA95501610050',  // should NOT be found since kuali record has - in right most 5
//    '-0050',            // yup
//    'FA9550-16-1-0050',  // yup
//    'DE-FC02-97ER62402', // nope
//    '97ER62402',         // yep
//    '207na27344',        // nope (skipper frag)
//    'DEAC5207NA27344',   // nope (skipper)
//    'FA9550-16-1___-005__##@#$#$#@_0',  // yup
    '20156700323460',  // yup
    '10-1110-NCAR'

    );
    test_awards_ids ($ids);
}

if (1) {
    $path = '/Users/ostwald/tmp/no_cache_ids.txt';
    $ids = get_ids_from_file($path);
    test_awards_ids ($ids);
}