"use strict";

define(['jquery', 'hashparamutils',
        'dbus!_', 'jquery.hashchange'], function($, hashparamutils, dbusProxy) {

    $.fn.paginatorify = function(url, additionalHashParams, context) {
        if (!this.length)
            return this;

        var hashParams = {};

        if (context === undefined)
            context = 3;

        var $loadingPageContent = $('<div>', {'class': 'loading-page'}).
            text("Loading page... please wait");

        var $elem = $(this);
        var numPages = 0;
        var $beforePaginator = null;
        var $afterPaginator = null;

        var currentRequest = null;

        function loadPage() {
            $elem.addClass('loading');
            $loadingPageContent.prependTo($elem);

            var hashCopy;
            if (additionalHashParams)
                hashCopy = $.extend(additionalHashParams(), hashParams);
            else
                hashCopy = hashParams;

            if (currentRequest !== null)
                currentRequest.abort();

            currentRequest = $.ajax({
                url: url,
                dataType: 'json',
                data: hashCopy,
                type: 'GET'
            }).done(function(result) {
                if ($beforePaginator)
                    $beforePaginator.detach();
                if ($afterPaginator)
                    $afterPaginator.detach();

                $loadingPageContent.detach();

                numPages = result.numpages;

                $beforePaginator = buildPaginator().addClass('before-paginator');
                $afterPaginator = buildPaginator().addClass('after-paginator');

                var $newContent = $(result.html);

                $elem.
                    removeClass('loading').
                    empty().
                    append($beforePaginator).
                    append($newContent).
                    append($afterPaginator).
                    trigger('page-loaded');
            });
        }

        function makeLink(pageNumber, styleClass, text) {
            styleClass = styleClass === undefined ? "" : styleClass;
            text = text === undefined ? pageNumber.toString() : text;

            var hp = $.extend({}, hashParams);
            hp.page = pageNumber;

            return $('<a>', {'class': 'number ' + styleClass,
                             'href': '#' + $.param(hp)}).text(text);
        }

        function buildPaginator() {
            var number = hashParams.page;
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
        }

        $(window).hashchange(function() {
            hashParams = hashparamutils.getHashParams();
            if (hashParams.page === undefined)
                hashParams.page = 1;
            else
                hashParams.page = parseInt(hashParams.page);

            if (hashParams.shell_version === undefined && dbusProxy.ShellVersion !== undefined)
                hashParams.shell_version = dbusProxy.ShellVersion;

            loadPage();
        });

        $(window).hashchange();

        this.bind('load-page', loadPage);

        return this;
    };

});
