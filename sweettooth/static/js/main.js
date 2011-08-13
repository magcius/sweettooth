"use strict";

require(['jquery', 'messages', 'jquery.jeditable'], function($, messages) {
    $.fn.csrfEditable = function(url) {
        var self = this;

        function error(xhr, status, error) {
            if (status == 403) {
                self.css("background-color", "#fcc");
            }
        }

        self.editable(url,
                      {submitdata: {csrfmiddlewaretoken: window._CSRF},
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

        $('#submit-ajax').click(function() {
            var $elem = $(this);

            var df = $.ajax({ url: $elem.data('url'),
                              type: 'POST',
                              data: {csrfmiddlewaretoken: window._CSRF}});
            df.done(function() {
                messages.addInfo("Your extension has been locked.").hide().slideDown();
                $elem.attr('disabled', true);
                $('h3, p.description').csrfEditable('disable').removeClass('editable');
            });

            return false;
        });

        if (window._SW)
            try {
                window._SW();
            } catch(e) {
                console.error(e);
            }
    });
});
