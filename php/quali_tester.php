<?php

include 'kuali.inc';

function test()
{
//$award_id = '1122-334-455';
//    $award_id = 'NA13OAR4310138'; // single full
//    $award_id = 'ACI-1448480'; // mulitple full
//$award_id = '1852977'; // single hit
//    $award_id = '52977'; // single partial hit
//    $award_id = '484--80'; // mulitple partial
//    $award_id = 'DE-FC02-97ER62402'; // false partial

//    $award_id = 'AGS0856145'; //
    $award_id = 'AGS1502208'; //


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


        $kuali_id = get_kuali_award_id($award_id, $match_criterion);
        print "\nkuali_id: $kuali_id\n";
    }
}

 test();