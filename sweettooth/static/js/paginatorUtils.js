"use strict";

define(['jquery', 'hashParamUtils'], function($, hashParamUtils) {

    var module = {};

    var makeLink = module.makeLink = function(pageNumber, styleClass, text) {
        styleClass = styleClass === undefined ? "" : styleClass;
        text = text === undefined ? pageNumber.toString() : text;

        var hp = hashParamUtils.getHashParams();
        hp.page = pageNumber;

        return $('<a>', {'class': 'number ' + styleClass,
                         'href': '#' + $.param(hp)}).text(text);
    };

    var buildPaginator = module.buildPaginator = function(page, numPages, context) {
        var number = page;
        var contextLeft = Math.max(number-context, 2);
        var contextRight = Math.min(number+context+2, numPages);

        var $elem = $('<div>', {'class': 'paginator-content'});

        if (number > 1) {
            makeLink(number-1, 'prev', '\u00ab').appendTo($elem);
            makeLink(1, 'first').appendTo($elem);
            if (number-context > 2)
                $elem.append($('<span>', {'class': 'ellipses'}).text("..."));

            for (var i = contextLeft; i < number; i++)
                makeLink(i).appendTo($elem);
        }

        $elem.append($('<span>', {'class': 'current number'}).text(number));

        if (number < numPages) {
            for (var i = number+1; i < contextRight; i++)
                makeLink(i).appendTo($elem);

            if (numPages - (number+context) > 2)
                $elem.append($('<span>', {'class': 'ellipses'}).text("..."));

            makeLink(numPages, 'last').appendTo($elem);
            makeLink(number+1, 'prev', '\u00bb').appendTo($elem);
        }

        return $('<div>', {'class': 'paginator'}).append($elem);
    };

    return module;

});
