<?php

/**
read a blob of candidate award_ids. If they aren't already in the cache, try to kuali-update them
and update the cache in the process
*/

include_once 'doi_tester.php';
include_once 'kuali.inc';

function update_kuali_cache($candidate_award_ids) {
    $kuali_cache = $GLOBALS['KUALI_RESPONSE_CACHE'];
//    $kuali_cache = get_kuali_response_cache();
    $num_cached_kuali_responses = count(array_keys($GLOBALS['KUALI_RESPONSE_CACHE']));

    echo ("before: $num_cached_kuali_responses\n");

    foreach ($candidate_award_ids as $award_id) {

        $award_id_key = is_numeric($award_id) ? (int)$award_id : $award_id;
        // test cache here
        echo ("testing $award_id_key\n");
        if (isset ($GLOBALS['KUALI_RESPONSE_CACHE'][$award_id_key])) {
            echo (" - key found\n");
            $cached_award_id = $GLOBALS['KUALI_RESPONSE_CACHE'][$award_id_key];
            if ($cached_award_id) {
                echo ("- using CACHED Kuali repsonse for $award_id: $cached_award_id\n");
            }
        } else {
            echo (" - key NOT found\n");
            $kuali_award_id = get_kuali_award_id ($award_id, $match_criterion);

            if ($kuali_award_id) {
                $GLOBALS['KUALI_RESPONSE_CACHE'][strval($award_id_key)] = $kuali_award_id;
            }
            else {
                $GLOBALS['KUALI_RESPONSE_CACHE'][strval($award_id_key)] = false;
            }
        }
    }

    echo ("after: " . count(array_keys($GLOBALS['KUALI_RESPONSE_CACHE'])) . "\n");

    if (count(array_keys($GLOBALS['KUALI_RESPONSE_CACHE'])) > $num_cached_kuali_responses) {
        if (1) {
            write_get_kuali_response_cache();
        } else {
            echo ("would have updated cache ...\n");
        }
    }
}

function get_award_ids($path) {
    $contents = file_get_contents($path);
    return array_filter(array_map('trim', explode("\n", $contents)));
}

//$award_ids = array ('ATM0342421', 'ATM0425247');
$award_ids = get_award_ids('/Users/ostwald/tmp/UNKNOWN_LEGACIES.txt');
echo (count($award_ids) . "ids\n");
update_kuali_cache($award_ids);