// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery'], function($) {
    "use strict";

    var exports = {};

    // Each table row has three columns:
    // ===================================================================
    // | Old Line Number | New Line Number | Diff |
    //
    // Each "buildChunk" function below should build full row(s).

    // For some reason it's hard to turn an array of jQuery objects into
    // one jQuery object.
    function flatten(list) {
        var $elems = $();
        $.each(list, function() {
            $elems = $elems.add(this);
        });
        return $elems;
    }

    function buildEqualChunk(chunk, oldContents, newContents) {
        function triggerCollapse() {
            // show() and hide() don't work on table-rows - jQuery
            // will set the row back to 'display: block'. Unsure if it's
            // a jQuery or browser bug.
            if (collapsed) {
                $triggerRow.removeClass('collapsed');
                $collapsable.css('display', 'table-row');
                $triggers.text('-');
            } else {
                $triggerRow.addClass('collapsed');
                $collapsable.css('display', 'none');
                $triggers.text('+');
            }

            collapsed = !collapsed;
        }

        var $triggerRow;
        var $triggers = $();
        var $collapsable = $();
        var collapsed = false;

        var $elems = $.map(chunk.lines, function(line, i) {
            var oldLinum = line[1];
            var newLinum = line[2];

            var contents = oldContents[oldLinum - 1];

            var $row = $('<tr>', {'class': 'diff-line equal'}).
                append($('<td>', {'class': 'old linum'}).text(oldLinum)).
                append($('<td>', {'class': 'new linum'}).text(newLinum)).
                append($('<td>', {'class': 'new contents'}).html(contents));

            if (chunk.collapsable) {
                if (i == 0) {
                    $triggerRow = $row;
                    $row.addClass('collapsable-trigger-row').find('.contents').each(function() {
                        var $trigger = $('<a>', {'class': 'collapsable-trigger'}).click(triggerCollapse);
                        $triggers = $triggers.add($trigger);
                        $(this).append($trigger);
                    });
                } else {
                    $row.addClass('collapsable-collapsed-row');
                    $collapsable = $collapsable.add($row);
                }
            }

            return $row;
        });

        if (chunk.collapsable)
            triggerCollapse($collapsable);

        return $elems;
    }

    // This is called for changes within lines in a 'replace' chunk,
    // one half-row at a time.  'contents' here is the line's contents
    //
    // If we replace:
    //     "this is a long, long line."
    //
    // with:
    //     "this is yet another long, long line."
    //
    // then we get regions that look like:
    //     [8, 9]  ,  [8, 13]
    // Our job is to highlight the replaced regions on the respective
    // half-row.
    function buildReplaceRegions(regions, contents) {
        function span(tag, text) {
            return $('<span>', {'class': 'diff-inline'}).addClass(tag).html(text);
        }

        function unchanged(text) { return span('unchanged', text); }
        function changed(text) { return span('changed', text); }

        // If there's no region, then SequentialMatcher failed to
        // find something useful, or we're in a regular delete/inserted
        // chunk. Highlight the entire region as unchanged.
        if (!regions || regions.length === 0)
            return unchanged(contents);

        var regionElems = [];
        var lastEnd = 0;

        $.each(regions, function() {
            var start = this[0], end = this[1];

            // The indexes in the 'regions' are the changed regions. We
            // can expect that the regions in between the indexes are
            // unchanged regions, so build those.

            regionElems.push(unchanged(contents.slice(lastEnd, start)));
            regionElems.push(changed(contents.slice(start, end)));

            lastEnd = end;
        });

        // We may have an unchanged region left over at the end of a row.
        if (contents.slice(lastEnd))
            regionElems.push(unchanged(contents.slice(lastEnd)));

        return regionElems;
    }

    function buildInsertLine(line, contents) {
        var linum = line[2];
        var content = contents[linum - 1];
        var region = line[4];

        return $('<tr>', {'class': 'diff-line inserted'}).
            append($('<td>', {'class': 'linum'})).
            append($('<td>', {'class': 'new linum'}).text(linum)).
            append($('<td>', {'class': 'new contents'}).
                     append(flatten(buildReplaceRegions(region, content))));
    }

    function buildInsertChunk(chunk, oldContents, newContents) {
        return $.map(chunk.lines, function(line) { buildInsertLine(line, newContents); });
    }

    function buildDeleteLine(line, contents) {
        var linum = line[1];
        var content = contents[linum - 1];
        var region = line[3];

        return $('<tr>', {'class': 'diff-line deleted'}).
            append($('<td>', {'class': 'old linum'}).text(linum)).
            append($('<td>', {'class': 'linum'})).
            append($('<td>', {'class': 'old contents'}).
                   append(flatten(buildReplaceRegions(region, content))));
    }

    function buildDeleteChunk(chunk, oldContents, newContents) {
        return $.map(chunk.lines, function(line) { buildDeleteLine(line, oldContents); });
    }

    function buildReplaceChunk(chunk, oldContents, newContents) {
        // Replace chunks are built up of a delete chunk and
        // an insert chunk, with special inline replace regions
        // for the inline modifications.

        var deleteChunk = [], insertChunk = [];

        $.each(chunk.lines, function() {
            var line = this;

            deleteChunk.push(buildDeleteLine(line, oldContents));
            insertChunk.push(buildInsertLine(line, newContents));
        });

        return [flatten(deleteChunk), flatten(insertChunk)];
    }

    var operations = {
        'equal': buildEqualChunk,
        'insert': buildInsertChunk,
        'delete': buildDeleteChunk,
        'replace': buildReplaceChunk
    };

    exports.buildDiffTable = function(chunks, oldContents, newContents) {
        var $table = $('<table>', {'class': 'code'});

        $.each(chunks, function() {
            $table.append(flatten(operations[this.change](this, oldContents, newContents)));
        });

        return $table;
    };

    return exports;
});
