"use strict";

define(['jquery', 'diff'], function($, diff) {

    var REVIEW_URL_BASE = '/review/ajax';

    var BINARY_TYPES = {};
    $.each(['mo', 'compiled'], function() {
        BINARY_TYPES[this] = true;
    });

    function isBinary(filename) {
        var parts = filename.split('.');
        var ext = parts[parts.length - 1];
        return BINARY_TYPES.hasOwnProperty(ext);
    }

    function buildFileView(data) {
        if (data.raw)
            return $(data.html);

        var $table = $('<table>', {'class': 'code'});

        $.each(data.lines, function(i) {
            $table.append($('<tr>', {'class': 'line'}).
                          append($('<td>', {'class': 'linum'}).text(i + 1)).
                          append($('<td>', {'class': 'contents'}).html(this)));
        });

        return $table;
    }

    function createDiffView(filename, pk) {
        var req = $.ajax({
            type: 'GET',
            dataType: 'json',
            data: { filename: filename },
            url: REVIEW_URL_BASE + '/get-file-diff/' + pk
        });

        var deferred = new $.Deferred();
        req.done(function(data) {
            deferred.resolve(diff.buildDiffTable(data.chunks, data.oldlines, data.newlines));
        });
        return deferred;
    }

    function createFileView(filename, pk) {
        var req = $.ajax({
            type: 'GET',
            dataType: 'json',
            data: { filename: filename },
            url: REVIEW_URL_BASE + '/get-file/' + pk
        });

        var deferred = new $.Deferred();
        req.done(function(data) {
            deferred.resolve(buildFileView(data));
        });
        return deferred;
    }

    $.fn.reviewify = function(diff) {
        var $elem = $(this);
        var $fileList = $('<ul>', {'class': 'filelist'}).appendTo($elem);
        var pk = $elem.data('pk');

        // Hide the file list until we're done grabbing all the elements.
        $fileList.hide();

        var $fileDisplay = $('<div>', {'class': 'filedisplay'}).appendTo($elem);
        $fileDisplay.css('position', 'relative');
 
        var currentFilename;
        var $currentFile = null;

        var req = $.ajax({
            type: 'GET',
            dataType: 'json',
            url: REVIEW_URL_BASE + '/get-file-list/' + pk,
        });

        function showTable(filename, $file, $selector) {
            $fileList.find('li a.fileselector').removeClass('selected');
            $selector.addClass('selected');

            $file.css('position', 'relative');

            if ($currentFile != null) {
                $currentFile.css({'position': 'absolute',
                                  'top': '0'});
                $currentFile.fadeOut();
                $file.fadeIn();
            } else {
                $file.show();
            }

            currentFilename = filename;
            $currentFile = $file;
        }

        req.done(function(files) {
            function createFileSelector(tag, filename) {
                var $selector = $('<a>').
                    addClass(tag).
                    addClass('fileselector').
                    text(filename);

                var $file = null;

                if (diff && isBinary(filename)) {
                    // We don't show binary files in the diff view.
                    return;
                }

                $('<li>').append($selector).appendTo($fileList);

                if (isBinary(filename)) {
                    $selector.addClass('binary');
                    return;
                }

                $selector.click(function() {
                    if ($selector.hasClass('selected'))
                        return;

                    if ($file === null) {
                        var d = (diff ? createDiffView : createFileView)(filename, pk, diff);
                        currentFilename = filename;
                        d.done(function($table) {
                            $file = $table;
                            $file.hide().appendTo($fileDisplay);
                            if (currentFilename === filename)
                                showTable(filename, $file, $selector);
                        });
                    } else {
                        showTable(filename, $file, $selector);
                    }

                });
            }

            $.each(files.changed, function() { createFileSelector('changed', this); });
            $.each(files.added, function() { createFileSelector('added', this); });
            $.each(files.deleted, function() { createFileSelector('deleted', this); });

            // Don't show the 'unchanged' section in a diff view.
            if (!diff)
                $.each(files.unchanged, function() { createFileSelector('unchanged', this); });

            $fileList.show();

            // Select the first item.
            $fileList.find('li a.fileselector').first().click();
        });
    };
});
