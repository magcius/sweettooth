"use strict";

require(['jquery', 'jquery.jeditable'], function($) {
    $.fn.csrfEditable = function(url, tok) {
        var self = this;

        function error(xhr, status, error) {
            if (status == 403) {
                self.css("background-color", "#fcc");
            }
        }

        self.editable(url,
                      {submitdata: {csrfmiddlewaretoken: tok},
                       ajaxoptions: {error: error},
                       data: function(string, settings) {
                           return $.trim(string, settings);
                       }});
        self.addClass("editable");
    };

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
