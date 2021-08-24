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
        test_award_id ($award_id);
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

if (count($argv) > 1) {
//    full_test_award_id($argv[1]);
    // test_award_id($argv[1]);
    find_unique_candidates($argv[1]);
}

if (0) {
    $ids = array(
        'NA13OAR43-101/38',
        '4310138',
        '13OAR4310138',
    );
    test_awards_ids ($ids);
}