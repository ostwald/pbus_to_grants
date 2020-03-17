function log(s) {
    if (window.console)
        console.log(s);
}



$(function () {

    $( "#accordion" ).accordion({
        heightStyle:"content",
        collapsible: true
    });

    $('button.award-id.kuali-word').click (function (event) {
        var $target = $(event.target);

        var award_id = $target.closest ('div.content').attr('id');
        log ("award_id " + award_id);
        var href = "https://stage.ucar.dgicloud.com/kuali?award_id=" + award_id;
        window.open (href, "kuali");
    })


    $('.context-link').click (function (event) {

        var pid = $(event.target).closest('.pub-row').attr("id");

        log ("context-link clicked: " + pid + "  (" + event.target.tagName + ")");

        if (event.target.tagName.toUpperCase() != 'A')
            return;

        $('tr.pub-row').removeClass('current');

        $('tr.pub-row#'+ pid).addClass ('current');


        // setTimeout (function () {
        //     $('tr.pub-row#'+ pid).addClass ('current');
        // }, 100)

        // return false;

    })

});