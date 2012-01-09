"use strict";

// FSUI is short for "Filtering and Sorting UI", which contains
// controls for filtering and sorting the extensions list

require(['jquery', 'hashparamutils', 'modal'], function($, hashparamutils, modal) {

    function makeLink(name, value, text) {
        return $('<li>', {'class': 'fsui-selection-link'}).
            text(text).
            click(function() {
                hashparamutils.setHashParam(name, value);
            });
    }

    var sortCriteria = {
        'name': "Name",
        'recent': "Recent",
        'downloads': "Downloads",
        'popularity': "Popularity"
    };

    $.fn.fsUIify = function() {

        return this.each(function() {
            var $elem = $(this);

            function closeUI() {
                if ($link.hasClass('selected')) {
                    $('.fsui').fadeOut('fast', function() {
                        $(this).detach();
                    });
                    $link.removeClass('selected');
                    return true;
                }
                return false;
            }

            var $link = $('<a>', {'class': 'fsui-link'}).
                text("Filtering and Sorting").
                click(function() {
                    $(this).addClass('selected');
                    var pos = $elem.offset();
                    var $fsui = $('<div>', {'class': 'fsui'}).
                        appendTo($elem).
                        hide().
                        fadeIn('fast');
                    modal.activateModal($fsui, closeUI);

                    var $sortUI = $('<div>', {'class': 'fsui-sort-ui'}).
                        appendTo($fsui).
                        append('<h4>Sort by</h4>');

                    var $sortUL = $('<ul>').appendTo($sortUI);
                    var sortLinks = {};
                    $.each(sortCriteria, function(key) {
                        sortLinks[key] = makeLink('sort', key, this).
                            appendTo($sortUL).
                            click(function() {
                                closeUI();
                            });
                    });

                    var hp = hashparamutils.getHashParams();
                    if (hp.sort === undefined)
                        hp.sort = 'name';

                    if (sortLinks.hasOwnProperty(hp.sort))
                        sortLinks[hp.sort].addClass('selected');

                    return false;
                }).appendTo($elem);
        });
    };
});
