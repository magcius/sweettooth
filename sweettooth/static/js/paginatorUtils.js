// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'hashParamUtils'], function($, hashParamUtils) {
    "use strict";

    var exports = {};

    function makeLink(pageNumber, styleClass, text) {
        styleClass = styleClass === undefined ? "" : styleClass;
        text = text === undefined ? pageNumber.toString() : text;

        var hp = hashParamUtils.getHashParams();
        hp.page = pageNumber;

        return $('<a>', {'class': 'number ' + styleClass,
                         'href': '#' + $.param(hp)}).text(text);
    }

    exports.buildPaginator = function(page, numPages, context) {
        var number = page;
        var contextLeft = Math.max(number-context, 2);
        var contextRight = Math.min(number+context+1, numPages);

        // If we're showing the ellipsis to emit one number,
        // just show the number instead.
        if (contextLeft === 3)
            contextLeft = 2;
        if (contextRight === numPages - 1)
            contextRight = numPages;

        var $elem = $('<div>', {'class': 'paginator-content'});

        if (number > 1) {
            makeLink(number-1, 'prev', '\u00ab').appendTo($elem);
            makeLink(1, 'first').appendTo($elem);
            if (contextLeft > 3)
                $elem.append($('<span>', {'class': 'ellipses'}).text("..."));

            for (var i = contextLeft; i < number; i++)
                makeLink(i).appendTo($elem);
        }

        $elem.append($('<span>', {'class': 'current number'}).text(number));

        if (number < numPages) {
            for (var i = number+1; i < contextRight; i++)
                makeLink(i).appendTo($elem);

            if (numPages - contextRight > 1)
                $elem.append($('<span>', {'class': 'ellipses'}).text("..."));

            makeLink(numPages, 'last').appendTo($elem);
            makeLink(number+1, 'prev', '\u00bb').appendTo($elem);
        }

        return $('<div>', {'class': 'paginator'}).append($elem);
    };

    return exports;
});
