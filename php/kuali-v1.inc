<?php
/**
 * Created by IntelliJ IDEA.
 * User: ostwald
 * Date: 2/6/19
 * Time: 9:46 AM
 *
 *  NOTE! This file should be identical to opensky module kuali_api.inc
 *
 */


/*
 * Returns object associated with provided award_id if
 * there is a single award returned by kuali API.
 * othewise, returns null.
 *
 * NOTE: kuali may return multiple items if there are multiple UCAR PI's for
 * a given grant. Therefore, we have to filter results for unique sponsorAwardId
 */
function get_kuali_award_info ($award_id, $match_criterion) {

    $kuali_resp = get_kuali_response($award_id);

    if (!isset ($kuali_resp[0])) {
        // this is an object, which means an empty result
        return null;
    }

    // eliminate duplate sponsorAwardIds (different people, same grant)
    if (count($kuali_resp) > 1) {
        $unique_ids = array();
        $filtered_resp = array();
        foreach ($kuali_resp as $item) {
            if (!in_array($item['sponsorAwardId'], $unique_ids)) {
                $filtered_resp[] = $item;
                $unique_ids[] = $item['sponsorAwardId'];
            }
        }
        $kuali_resp = $filtered_resp;
    }

    // if there is more than 1 survivor - FAIL
    // NOTE: is this really what we want to do?
    // NO! it is possible that FAINIDs 
    if (count ($kuali_resp) != 1) {
        print 'FAIL: Count is ' . count ($kuali_resp) . ' for AWARD_ID: ' . $award_id . "\n";
        print_r ($kuali_resp);
        return null;
    }

    if ($match_criterion == 'NAIVE_PARTIAL') {
        // Niave partial
        return $kuali_resp[0];
    }

    else if ($match_criterion == 'STRICT') {
        return $kuali_resp[0]['matchType'] == 'full' ? $kuali_resp[0] : null;
    }

    else if ($match_criterion == 'SMART_PARTIAL') {
        if ($kuali_resp[0]['matchType'] == 'full') {
            return $kuali_resp[0];
        }
        // now try to match all non-special query chars with sponsorAwardId
        $kuali_award_id = preg_replace("/[^A-Za-z0-9 ]/", '', $kuali_resp[0]['sponsorAwardId']);
        $sought_award_id = preg_replace("/[^A-Za-z0-9 ]/", '', $award_id);
        if (endsWith ($kuali_award_id, $sought_award_id)) {
            return $kuali_resp[0];
        } else {
            return null;
        }
    }

    // Strict

}

/*
 * returns kauli response for proviced $award_id as object or array
 */
function get_kuali_response($award_id) {

        echo "get_kuali_response: $$award_id\n";

    $base_url = 'http://fatomcat-test.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid';
    $username = 'openskykcapi';
    $password = 'W!n+er5now#';

//    $auth_string = 'Basic ' . base64_encode("$username:$password");

    $ch = curl_init();
    $options = array(
        CURLOPT_URL => $base_url.'?sponsorAwardId='.$award_id,
        CURLOPT_USERPWD => $username . ":" . $password,
        CURLOPT_RETURNTRANSFER => 1
    );

    curl_setopt_array($ch, $options);
    $resp = curl_exec($ch);
    curl_close($ch);

    $response = json_decode($resp, true);

//    print json_encode($response, JSON_PRETTY_PRINT);

    return $response;

}

function endsWith($haystack, $needle) {
    $length = strlen($needle);
    if ($length == 0) {
        return true;
    }

    return (substr($haystack, -$length) === $needle);
}


function test ()
{
    //$award_id = '1122-334-455';
//    $award_id = 'NA13OAR4310138'; // single full
//    $award_id = 'ACI-1448480'; // mulitple full
    //$award_id = '1852977'; // single hit
//    $award_id = '52977'; // single partial hit
//    $award_id = '484--80'; // mulitple partial
//    $award_id = 'DE-FC02-97ER62402'; // false partial

    $award_id = '2015-67003-23489'; //



    print "------------------\n$award_id\n";
    if (1) {
        $response = get_kuali_response($award_id);
        print ("\nRESPONSE\n");
        print_r($response);
    }

    if (1) {
        $match_criterion = 'SMART_PARTIAL';
        $info = get_kuali_award_info($award_id, $match_criterion);
        print "\nINFO\n";
        print_r($info);
    }
}

// test();