// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'hashParamUtils', 'paginatorUtils', 'dbus!_', 'templates', 'jquery.hashchange'], function($, hashParamUtils, paginatorUtils, dbusProxy, templates) {
    "use strict";

    $.fn.paginatorify = function(context) {
        if (!this.length)
            return this;

        if (context === undefined)
            context = 3;

        var $elem = $(this);
        var $beforePaginator = null;
        var $afterPaginator = null;

        var currentRequest = null;

        function loadPage() {
            if (currentRequest !== null)
                currentRequest.abort();

            if ($beforePaginator !== null)
                $beforePaginator.addClass('loading');

            var queryParams = hashParamUtils.getHashParams();
            if (queryParams.page === undefined)
                queryParams.page = 1;
            if (queryParams.shell_version === undefined)
                queryParams.shell_version = dbusProxy.ShellVersion;
            if ($('#search_input').val())
                queryParams.search = $('#search_input').val();

            currentRequest = $.ajax({
                url: '/extension-query/',
                dataType: 'json',
                data: queryParams,
                type: 'GET'
            }).done(function(result) {
                if ($beforePaginator)
                    $beforePaginator.detach();
                if ($afterPaginator)
                    $afterPaginator.detach();

                var page = parseInt(queryParams.page, 10);
                var numPages = result.numpages;

                var $paginator = paginatorUtils.buildPaginator(page, numPages, context);
                $beforePaginator = $paginator.clone().addClass('before-paginator');
                $afterPaginator = $paginator.clone().addClass('after-paginator');
                $paginator.empty();

                $.each(result.extensions, function() {
                    // Serialize out the svm as we want it to be JSON
                    // in the data attribute.
                    this.shell_version_map = JSON.stringify(this.shell_version_map);

                    if (this.description)
                        this.first_line_of_description = this.description.split('\n')[0];
                });

                var $newContent = $(templates.get('extensions/info_list')(result));

                $elem.
                    removeClass('loading').
                    empty().
                    append($beforePaginator).
                    append($newContent).
                    append($afterPaginator).
                    trigger('page-loaded');
            });
        }

        $(window).hashchange(loadPage);

        this.on('load-page', loadPage);

        return this;
    };

});
