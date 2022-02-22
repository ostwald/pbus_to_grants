<?php

function get_ISO_date_string ($timestamp) {
    return date("Y-m-d\TH:i:s", $timestamp) .'.000Z';
}

function ISO_to_human_readable($iso_date_string) {
    return date('Y-m-d', strtotime($iso_date_string));
}

function date_string_to_timestamp($date_string) {
    return strtotime($date_string);
}


$mystamp = strtotime("-1 week");
$my_ISO = get_ISO_date_string($mystamp);

print $mystamp . "\n";
print "my ISO: $my_ISO\n";
$my_new_stamp = date_string_to_timestamp($my_ISO);
print "my new stamnp: $my_new_stamp\n";

$simple_date_string = "8/10/2021";
$simple_timestamp = date_string_to_timestamp($simple_date_string);
$simple_ISO = get_ISO_date_string($simple_timestamp);
print "simple ISO: $simple_ISO\n";

$start = $simple_date_string;
echo date('Y-m-d H:i',strtotime('+3 hour +20 minutes',strtotime($start)));
echo "\ndone\n--------------------\n";

// We start at "end-date" and make intervals that stretch backwards
$end_date_string = '8/1/2021';
$end_date = strtotime($end_date_string);
print "starting at $end_date_string and working backwards ...\n";
$duration = 2; // weeks that is
$unit = "weeks";
$num_periods = 3;

foreach (range(1, $num_periods+1) as $period) {
    $delta_clause = "-".($period * $duration) . $unit;
    print "\ndate clause: $delta_clause\n";
    $start_date = strtotime($delta_clause, $end_date);
    print "period $period - start: " . date('Y-m-d H:i', $start_date) . "\n";;
}