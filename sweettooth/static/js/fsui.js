"use strict";

// FSUI is short for "Filtering and Sorting UI", which contains
// controls for filtering and sorting the extensions list

require(['jquery', 'hashparamutils', 'modal'], function($, hashparamutils, modal) {

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
                    $('.fsui-dropdown').fadeOut('fast', function() {
                        $(this).detach();
                    });
                    $link.removeClass('selected');
                    return true;
                }
                return false;
            }

            var hp = hashparamutils.getHashParams();
            if (hp.sort === undefined || !sortCriteria.hasOwnProperty(hp.sort))
                hp.sort = 'name';

            var $fsui = $('<div>', {'class': 'fsui'}).appendTo($elem);

            $fsui.append('<span>Sort by</span>');

            var $link = $('<a>', {'class': 'fsui-dropdown-link'}).
                append($('<span>').text(sortCriteria[hp.sort])).
                append($('<span>', {'class': 'fsui-dropdown-link-arrow'}).text('\u2304')).
                click(function() {
                    $(this).addClass('selected');
                    var $dropdown = $('<div>', {'class': 'fsui-dropdown'}).
                        appendTo($elem).
                        hide().
                        fadeIn('fast');
                    modal.activateModal($dropdown, closeUI);

                    var $sortUI = $('<div>').appendTo($dropdown);

                    var $sortUL = $('<ul>').appendTo($sortUI);
                    var sortLinks = {};
                    $.each(sortCriteria, function(key) {
                        sortLinks[key] = $('<li>', {'class': 'fsui-dropdown-item'}).
                            text(this).
                            appendTo($sortUL).
                            click(function() {
                                hashparamutils.setHashParam('sort', key);
                                closeUI();
                            });
                    });

                    sortLinks[hp.sort].addClass('selected');

                    return false;
                }).appendTo($fsui);
        });
    };
});
