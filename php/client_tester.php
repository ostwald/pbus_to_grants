<?php
/**
 * Created by IntelliJ IDEA.
 * User: ostwald
 * Date: 12/11/19
 * Time: 10:36 AM
 */

include 'kuali.inc';


function get_kuali_response_tester ($award_id)
{

    $resp = get_kuali_response($award_id);

    print 'response is a ' . gettype($resp) ."\n";

    print_r($resp);
}


function parse_kuali_award_info_tester ($award_id) {
    $kuali_resp = get_kuali_response($award_id);
    $resp = parse_kuali_award_info ($award_id, $kuali_resp, $match_criterion);
    print 'response is a ' . gettype($resp) ."\n";
    print_r($resp);

}



// $award_id = 'NA13OAR4310138'; // 2 hits
// $award_id = 'DE-SC0012711';  // 1 hit
// $award_id = 'SC0012711';  // 1 hit partial
// $award_id = 'SC0012711x';  // 0 hit
# $award_id = '';
# $award_id = 'DEAC0576RL01830';  # skpped
$award_id = '1755088';  # 17 hits
//$award_id = null;


// get_kuali_response_tester($award_id);
parse_kuali_award_info_tester($award_id);