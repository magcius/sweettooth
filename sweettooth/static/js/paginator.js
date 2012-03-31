// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'hashParamUtils', 'paginatorUtils', 'dbus!_', 'templates'], function($, hashParamUtils, paginatorUtils, dbusProxy, templates) {
    "use strict";

    $.fn.paginatorify = function(context) {
        if (!this.length)
            return this;

        if (context === undefined)
            context = 3;

        var $loadingPageContent = $(templates.paginator.loading_page());

        var $elem = $(this);
        var $beforePaginator = null;
        var $afterPaginator = null;

        var currentRequest = null;

        function loadPage() {
            $elem.addClass('loading');
            $loadingPageContent.prependTo($elem);

            if (currentRequest !== null)
                currentRequest.abort();

            var queryParams = hashParamUtils.getHashParams();
            if (queryParams.page === undefined)
                queryParams.page = 1;
            if (queryParams.shell_version === undefined)
                queryParams.shell_version = dbusProxy.ShellVersion;
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

                $loadingPageContent.detach();

                var page = queryParams.page;
                var numPages = result.numpages;

                var $paginator = paginatorUtils.buildPaginator(page, numPages, context);
                $beforePaginator = $paginator.clone().addClass('before-paginator');
                $afterPaginator = $paginator.clone().addClass('after-paginator');
                $paginator.empty();

                // Serialize out the svm as we want it to be JSON in the data attribute.
                $.each(result.extensions, function() {
                    this.shell_version_map = JSON.stringify(this.shell_version_map);
                });

                var $newContent = $(templates.extensions.info_list(result));

                $elem.
                    removeClass('loading').
                    empty().
                    append($beforePaginator).
                    append($newContent).
                    append($afterPaginator).
                    trigger('page-loaded');
            });
        }

        this.bind('load-page', loadPage);

        return this;
    };

});
