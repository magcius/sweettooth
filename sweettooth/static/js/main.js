"use strict";

require(['jquery', 'messages', 'extensions', 'paginator',
         'jquery.cookie', 'jquery.jeditable',
         'jquery.timeago', 'jquery.rating'], function($, messages) {
    if (!$.ajaxSettings.headers)
        $.ajaxSettings.headers = {};

    $.ajaxSettings.headers['X-CSRFToken'] = $.cookie('csrftoken');

    $.fn.csrfEditable = function(url, options) {
        return $(this).each(function() {
            var $elem = $(this);

            function error(xhr, status, error) {
                if (status == 403) {
                    $elem.css("background-color", "#fcc");
                }
            }

            $elem.editable(url, $.extend(options || {},
                                { select: true,
                                  onblur: 'submit',
                                  ajaxoptions: { error: error, dataType: 'json' },
                                  callback: function(result, settings) {
                                      $elem.text(result);
                                  },
                                  data: function(string, settings) {
                                      return $.trim(string);
                                  }}));
            $elem.addClass("editable");
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
            });

            return false;
        });

        $('#local_extensions').addLocalExtensions();
        $('#error_report').fillInErrors();
        $('.extension.single-page').addExtensionSwitch();
        $('.comment .rating').each(function() {
            $(this).find('input').rating();
        });
        $('form .rating').rating();

        $('.expandy_header').click(function() {
            $(this).toggleClass('expanded').next().slideToggle();
        }).not('.expanded').next().hide();

        $('#extension_shell_versions_info').buildShellVersionsInfo();

        $('.extension_status_toggle a').click(function() {
            var $link = $(this);
            var $tr = $link.parents('tr');
            var href = $link.attr('href');
            var pk = $tr.data('pk');
            var $ext = $link.parents('.extension');

            var req = $.ajax({
                type: 'GET',
                dataType: 'json',
                data: { pk: pk },
                url: href
            });

            req.done(function(data) {
                $ext.data('svm', data.svm);
                $('#extension_shell_versions_info').buildShellVersionsInfo();
                $tr.find('.mvs').html(data.mvs);
                $tr.find('.extension_status_toggle').toggleClass('visible');
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
