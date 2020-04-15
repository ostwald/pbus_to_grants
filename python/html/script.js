function log(s) {
    if (window.console)
        console.log(s);
}

$(function () {

    $('#sort-button').click(function (event) {
        log ("sort button clicked");
        // sort_table ('kuali_verified_award_ids', -1);
        sort_table ('pub_date', -1);
    })


//    $('table.data-table td').click (function (event) {
    $('table.data-table a').click (function (event) {
        var $tr = $(event.target).closest('tr')
        var pid = $tr.attr('id')
        $('table.data-table tr').removeClass('current');
        $('table.data-table tr#'+ pid).addClass ('current');
    })

    function sort_table (field, asc) {
        var rows = $('table.data-table tbody tr');
        log (rows.length + ' rows found')

        log (rows);

        rows.sort(function(a, b) {

            var A = getVal(a);
            var B = getVal(b);

            if(A < B) {
                return -1*asc;
            }
            if(A > B) {
                return 1*asc;
            }
            return 0;
        });


        function getVal(elm) {
            var $elm = $(elm);
            if ($elm.hasClass('header')) {
                log('HEADER');
                return asc == 1 ? '' : 'zzz'
            }
            if (field == 'doi') {
                return $elm.find("td.doi a").text();
            }
            if (field == 'pid') {
                return $elm.find("td.pid a").text();
            }
            if (field == 'kuali_verified_award_ids') {
                return $elm.find("td.kuali_verified_award_ids ul li a").text()
            }

        }

        $('table.data-table tbody').empty();


        $.each(rows, function(index, row) {
            $('table.data-table tbody').append($(row));
        });

    }


});