"use strict";

require(['jquery', 'messages', 'jquery.cookie', 'jquery.jeditable'], function($, messages) {
    if (!$.ajaxSettings.headers)
        $.ajaxSettings.headers = {};

    $.ajaxSettings.headers['X-CSRFToken'] = $.cookie('csrftoken');

    $.fn.csrfEditable = function(url) {
        var self = this;

        function error(xhr, status, error) {
            if (status == 403) {
                self.css("background-color", "#fcc");
            }
        }

        self.editable(url, { select: true,
                             ajaxoptions: { error: error },
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

        function closeUserSettings() {
            var needsClose = $('#global_domain_bar .user').hasClass('active');
            if (!needsClose)
                return false;

            $('#global_domain_bar .user').removeClass('active');
            $('#global_domain_bar .user_settings').animate({ top: '10px', opacity: 0 }, 200, function() {
                $(this).hide();
            });
            return true;
        }

        function openUserSettings() {
            $('#global_domain_bar .user').addClass('active');
            $('#global_domain_bar .user_settings').show().css({ top: '-10px', opacity: 0 }).animate({ top: '0', opacity: 1 }, 200);
        }

        $(document.body).click(function() {
            if (closeUserSettings())
                return false;
        });

        $('#global_domain_bar .user_settings').click(function(e) {
            e.stopPropagation();
        });

        $('#global_domain_bar .user').click(function() {
            if ($(this).hasClass('active')) {
                closeUserSettings();
            } else {
                openUserSettings();
            }
            return false;
        });

        $('#submit-ajax').click(function() {
            var $elem = $(this);

            var df = $.ajax({ url: $elem.data('url'),
                              type: 'POST' });
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
                if (console && console.error)
                    console.error(e);
            }
    });
});
