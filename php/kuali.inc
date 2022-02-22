<?php
/**
 * Created by IntelliJ IDEA.
 * User: ostwald
 * Date: 2/6/19
 * Time: 9:46 AM
 *
 *  NOTE! This file should be identical to openskydora module kuali_api.inc
 *
 */

$skip_award_ids = null;

function get_skip_award_ids () {
    return array (
        '999999',
        'DEAC0576L01830',
        'DEAC0576RL01830',
        'DEAC5207NA27344',
        'DEAC0500OR22725',
        'DEAC3608GO28308',
    );
}

// -----------------------------------------------------------
// Kuali common code below this line!!

/**
 * Remove non-alpha/numeric characters (see regex) from given raw_award_id. Used to compare IDs
 * e.g., to compare a given award_id with a kuali_id to determine if they match, even
 * though they may not be identical.
 * For example, DEAC5207NA27344 would match with 7na27344.
 *
 * @param $raw
 * @return mixed
 */
function sanitize_id ($raw_award_id) {
    return strtoupper(preg_replace("/[^A-Za-z0-9]/", '', $raw_award_id));
}

/**
  An opportunity to alter a given award id to aid the kuali match. Called
  before the query award id is submitted to kuali.
  */
function preprocess_award_id($raw_award_id) {
    /*  super Kludge - Kuali will not valiate AGS-0856145,
        which is the cooperative agreement and is found in many
        records (and on the web). Kuali does recognize ATM0856145
        which is the same award.
        This KLudge allows kuali to recognize AGS-0856145
    */
    if (endswith($raw_award_id, '0856145')) {
        return '0856145';
    }
    return $raw_award_id;
}

/**
 * get the award_id stored in Kuali for a match with provided award_id.
 * note - the provided, or query, award_id may not exactly match a kuali_id.
 * @param $award_id - provided, or query, award_id
 * @param $match_criterion
 * @return the kuali award_id that was matched, or null if there is no match
 */
function get_kuali_award_id ($award_id, $match_criterion="SMART_PARTIAL") {
//    print "get_kuali_award_id: $award_id\n";

    $award_id = preprocess_award_id($award_id);

    // award info is the return from the Kuali API containing possibly many
    // hits
    $match_info = get_kuali_award_info ($award_id, $match_criterion);
    if (!$match_info) {
//        print "no matching kuali record found\n";
        return null;
    }

    return match_id_from_kuali_record ($award_id, $match_info);
}

/*
 * Returns object associated with provided award_id if
 * there is a single award returned by kuali API.
 * othewise, returns null.
 *
 * NOTE: kuali may return multiple items if there are multiple UCAR PI's for
 * a given grant. Therefore, we have to filter results for unique sponsorAwardId
 */
function get_kuali_award_info ($award_id, $match_criterion="SMART_PARTIAL") {
    $kuali_resp = get_kuali_response($award_id);
    return parse_kuali_award_info ($award_id, $kuali_resp, $match_criterion);
}


/**
    return the Kuali_id in the kuali record that matches with the $award_id, or
    null if a match is not found
    */
function match_id_from_kuali_record ($award_id, $kuali_record) {
    $fields_to_check = array ('sponsorAwardId', 'fainId');
    $query_award_id = sanitize_id ($award_id);

//    print json_encode($kuali_record, JSON_PRETTY_PRINT) ."\n";

    foreach($fields_to_check as $field) {
        $kuali_award_id = $kuali_record[$field];
        $sanitzed_kuali_award_id = sanitize_id($kuali_award_id);
        if (endsWith($sanitzed_kuali_award_id, $query_award_id) ||
            endsWith($query_award_id, $sanitzed_kuali_award_id)) {

            if (is_skip_id ($kuali_award_id)) {
                print "  - rejecting a skipped_id - $kuali_award_id\n";
            }

            return is_skip_id ($kuali_award_id) ? null : $kuali_award_id;
        }
    }
    return null;
}

/*
 * Returns single Kuali API result for provided award_id if possible, null otherwise.
 *
 * kuali_resp is response from API, which may include several candidates (Kuali
 * API matches against 5 righTmost characters of award_id). This function must
 * choose the best match if there more than 1 candidates.
 */
function parse_kuali_award_info ($award_id, $kuali_resp, $match_criterion="SMART_PARTIAL") {

    if (!isset ($kuali_resp[0])) {
        // this is an object, which means an empty result
        return null;
    }

    // we're dealing with an array
    $len_results = count($kuali_resp);

    if ($len_results == 0) {
        return null;
    }

    // return first result with matchType == full (test for STRICT first)
    foreach ($kuali_resp as $result) {
        if ($result['matchType'] == 'full') {
            return $result;
        }
    }

    if ($match_criterion == 'STRICT') {
        return null;
    }

    // if criteria is NOT STRICT, return first result that meets SMART_PARTIAL criteria
    foreach ($kuali_resp as $result) {

        // SMART_PARTIAL: try to match all non-special query chars with sponsorAwardId
        // look in sponsorAwardId and fainId for partial patch

        $kuali_id = match_id_from_kuali_record($award_id, $result);
//        print "kuali_id: $kuali_id";
        if ($kuali_id) {
            return $result;
        }
    }

    // there are no strict matches and no SMART_PARTIAL matches
    // if the match_criteria is NAIVE_PARTIAL just return the first result
    // (if there is one) since all results are NAIVE_PARTIAL
    if ($match_criterion == 'NAIVE_PARTIAL') {
        return $kuali_resp[0];
    }

    return null;
}

/* cache the skip array */
function is_skip_id ($award_id) {
    if (!isset($GLOBALS['skip_award_ids'])) {
        $GLOBALS['skip_award_ids'] = get_skip_award_ids();
    }
    return in_array ($award_id, $GLOBALS['skip_award_ids']);
}

/*
 * returns kauli response for provided $award_id as object or array
 */
function get_kuali_response($award_id) {

    $base_url = 'https://www.fin.ucar.edu/kualiapi/awardsbysponsorawardid';
//    $base_url = 'http://fatomcat-test.fin.ucar.edu:8081/kualiapi/awardsbysponsorawardid';
    $username = 'openskykcapi';
    $password = 'W!n+er5now#';

    $ch = curl_init();

    $options = array(
        CURLOPT_URL => $base_url.'?sponsorAwardId='.make_query_id($award_id),
        CURLOPT_USERPWD => $username . ":" . $password,
        CURLOPT_RETURNTRANSFER => 1
    );

    curl_setopt_array($ch, $options);
    $resp = curl_exec($ch);
    curl_close($ch);

    $response = json_decode($resp, true);

//    print json_encode($response, JSON_PRETTY_PRINT) ."\n";

    return $response;

}

function endsWith($haystack, $needle) {
    $length = strlen($needle);
    if ($length == 0) {
        return true;
    }

    return (substr($haystack, -$length) === $needle);
}

/**
 * return the last 5 characters of the provided award_id, after it has
 * been normalized to exclude non-alphas (but leave dashes in because Kuali
 * leaves them in!!)
 */
function make_query_id ($award_id) {
    // important - leave dashes in
    $normalized = preg_replace("/[^A-Za-z0-9\-]/", '', $award_id);

    if (strlen($normalized) < 5) {
        return $award_id;
    } else {
        return strtoupper(substr($normalized, -5));
    }
}
