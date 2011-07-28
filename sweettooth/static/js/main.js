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

    function setTagEnabled(uuid, tag, enabled) {
        var url = '/browse/ajax/modifytag/' + tag;
        return $.ajax({
            url: url,
            dataType: 'json',
            data: {'uuid': elem.data('uuid'),
                   'action': enabled ? 'add' : 'rm'}
        });
    }

    $.fn.featureToggleify = function(init) {
        var elem = $(this);
        elem.bind('feature-status-changed', function(e, isFeatured) {
            elem.data('feature-status', isFeatured);
            if (isFeatured)
                elem.text("Unfeature extension");
            else
                elem.text("Feature extension");
        }).click(function() {
            var d = setTagEnabled(elem.data('uuid'),
                                  'featured',
                                  !elem.data('feature-status'));
            d.done(function(data) {
                e.trigger('feature-status-changed', data);
            });
        }).trigger('feature-status-changed', init);
    };

});
