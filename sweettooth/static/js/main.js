"use strict";

require(['jquery', 'jquery.timeago', 'jquery.rating', 'buttons'], function($) {
    $(document).ready(function() {
        // Make the login link activatable.
        $("#login_link").click(function(event) {
            $(this).toggleClass('selected');
            $("#login_popup_form").slideToggle();
            return false;
        });

        if (window._SW)
            window._SW();
    });
});
