"use strict";

require(['jquery', 'main', 'review'], function($) {
    $(document).ready(function() {
        $("#files").reviewify(false);
        $("#diff").reviewify(true);
        $("h2").click(function() {
            $(this).toggleClass("expanded").next().slideToggle();
        }).not(".expanded").next().hide();
    });
});
