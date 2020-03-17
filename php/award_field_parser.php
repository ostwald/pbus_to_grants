<?php

/*
    accept a "field value" which may be an award_id and may be a longer phrase
    that possibly contains an awware_id
*/

/**
 * Remove items that are right-most substrings of another item in the given array
 *
 * @param $award_ids
 */
function dedup_award_ids ($award_ids) {
    $award_ids = array_unique($award_ids);
    $deduped = array();
    forEach ($award_ids as $candidate) {
        print "- candidate: $candidate\n";
        $is_right_subset = false;
        forEach ($award_ids as $id) {
            print "  - id: $id\n";
            if ((strlen($id) > strlen($candidate)) && endswith($id, $candidate)) {
                $is_right_subset = true;
                print '  --- is_right_subset!' . "\n";
            }
        }
        if (!$is_right_subset) {
            $deduped[] = $candidate;
        }
    }
    return $deduped;
}

function endsWith($haystack, $needle) {
    $length = strlen($needle);
    if ($length == 0) {
        return true;
    }

    return (substr($haystack, -$length) === $needle);
}

function get_award_id_tokens ($value) {
    $values = array_filter(array_map('get_award_id', explode(" ", $value)));
//    print_r($values);
    return $values;

//    $splits = explode(" ", $value);
//
//    echo "SPLITS\n";
//    print_r($splits);
//
//    $tokens = array_map('get_award_id', $splits);
//    echo "TOKENS\n";
//    print_r($splits);
//
//    $filtered = array_filter($tokens);
//    echo "FILTERED\n";
//    print_r($filtered);
//
//    return $filtered;

}

function get_award_id ($value) {

    $val = preg_replace("/[^A-Za-z0-9 ]/", '', $value);

    if (strlen($val) < 5) {
        return null;
    }

    // if it doesn't have a number, reject it
    preg_match("/[0-9]/", $val, $matches);
//    print "MATCHES\n";
//    print_r($matches);
//
//    print "=> " . sizeof($matches) . "\n";

//    if (sizeof($matches) < 1) {
//        return null;
//    }
//
//    return $val;

    return (sizeof($matches) < 1) ? null : $val;
}


function tokenize_tester()
{

    $award_id_phrase_1 = 'difo2lasodf delad5sdfasdf 299-d4944iu #12345';
    $award_id_phrase_2 = '4590di eidkkslakds 54-094004-049';

    $fooberries = array($award_id_phrase_1, $award_id_phrase_2);

    $tokens = array();
    foreach ($fooberries as $award_id_phrase) {
        $tokens = array_merge($tokens, get_award_id_tokens($award_id_phrase));
        //    $tokens += get_award_id_tokens($award_id_phrase));
    }


    //$tokens = array_map ('get_award_id_tokens',  $fooberries);


    //$tokens = get_award_id_tokens($foo);

    print "FINAL\n";
    print_r($tokens);
}

$test_array = array(
    'hello',
    'jhello',
    'hella',
    'ella',
    'hella',
    'lo',
    );

print_r (dedup_award_ids($test_array));