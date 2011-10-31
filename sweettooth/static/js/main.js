"use strict";

require(['jquery', 'messages', 'jquery.cookie', 'jquery.jeditable', 'jquery.timeago'], function($, messages) {
    if (!$.ajaxSettings.headers)
        $.ajaxSettings.headers = {};

    $.ajaxSettings.headers['X-CSRFToken'] = $.cookie('csrftoken');

    $.fn.csrfEditable = function(url) {
        return this.each(function() {
            var elem = $(this);

            function error(xhr, status, error) {
                if (status == 403) {
                    elem.css("background-color", "#fcc");
                }
            }

            elem.editable(url, { select: true,
                                 ajaxoptions: { error: error, dataType: 'json' },
                                 callback: function(result, settings) {
                                     elem.text(result);
                                 },
                                 data: function(string, settings) {
                                     return $.trim(string);
                                 }});
            elem.addClass("editable");
        });
    };

    $(document).ready(function() {
        // Make the login link activatable.
        $("#login_link").click(function(event) {
            $(this).toggleClass('selected');
            $("#login_popup_form").slideToggle();
            return false;
        });

        $("abbr.timestamp").timeago();

        function closeUserSettings() {
            var needsClose = $('#global_domain_bar .user').hasClass('active');
            if (!needsClose)
                return false;

            $('#global_domain_bar .user').removeClass('active');
            $('#global_domain_bar .user_settings, #global_domain_bar .login_popup_form').animate({ top: '10px', opacity: 0 }, 200, function() {
                $(this).hide();
            });
            return true;
        }

        function openUserSettings() {
            $('#global_domain_bar .user').addClass('active');
            $('#global_domain_bar .user_settings, #global_domain_bar .login_popup_form').show().css({ top: '-10px', opacity: 0 }).animate({ top: '0', opacity: 1 }, 200);
        }

        $(document.body).click(function() {
            if (closeUserSettings())
                return false;
        });

        $('#global_domain_bar .user_settings, #global_domain_bar .login_popup_form').click(function(e) {
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
                messages.addInfo("Your extension has been submitted.").hide().slideDown();
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
