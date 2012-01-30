"use strict";

define(['jquery'], function($) {

    // Each table row has four columns:
    // ===================================================================
    // | Old Line Number | Old Contents | New Line Number | New Contents |
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
        return $.map(chunk.lines, function(line, i) {
            var oldLinum = line[1];
            var newLinum = line[2];

            var contents = oldContents[oldLinum - 1];

            var $row = $('<tr>', {'class': 'line equal'}).
                append($('<td>', {'class': 'old linum'}).text(oldLinum)).
                append($('<td>', {'class': 'old contents'}).html(contents)).
                append($('<td>', {'class': 'new linum'}).text(newLinum)).
                append($('<td>', {'class': 'new contents'}).html(contents));

            if (chunk.collapsable) {
                if (i == 0)
                    $row.addClass('collapsable-first');
                else
                    $row.addClass('collapsable-rest');
            }

            return $row;
        });
    }

    function buildInsertChunk(chunk, oldContents, newContents) {
        return $.map(chunk.lines, function(line) {
            var linum = line[2];
            var contents = newContents[linum - 1];

            return $('<tr>', {'class': 'line inserted'}).
                append($('<td>', {'class': 'linum'})).
                append($('<td>')).
                append($('<td>', {'class': 'new linum'}).text(linum)).
                append($('<td>', {'class': 'new contents'}).html(contents));
        });
    }

    function buildDeleteChunk(chunk, oldContents, newContents) {
        return $.map(chunk.lines, function(line) {
            var linum = line[1];
            var contents = newContents[linum - 1];

            return $('<tr>', {'class': 'line deleted'}).
                append($('<td>', {'class': 'old linum'}).text(linum)).
                append($('<td>', {'class': 'old contents'}).html(contents)).
                append($('<td>', {'class': 'linum'})).
                append($('<td>'));
        });
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
            return $('<span>', {'class': 'inline'}).addClass(tag).html(text);
        }

        function unchanged(text) { return span('unchanged', text); }
        function changed(text) { return span('changed', text); }

        // If there's no region, then SequentialMatcher failed to
        // find something useful (or the ratio was too low). Just
        // highlight the entire region as changed.
        if (!regions || regions.length === 0)
            return changed(contents);

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

    function buildReplaceChunk(chunk, oldContents, newContents) {
        return $.map(chunk.lines, function(line) {
            var oldLinum = line[1], newLinum = line[2];
            var oldRegion = line[3], newRegion = line[4];

            var oldContent = oldContents[oldLinum - 1];
            var newContent = newContents[newLinum - 1];

            return $('<tr>', {'class': 'line replaced'}).
                append($('<td>', {'class': 'old linum'}).text(oldLinum)).
                append($('<td>', {'class': 'old contents'})
                       .append(flatten(buildReplaceRegions(oldRegion, oldContent)))).
                append($('<td>', {'class': 'new linum'}).text(newLinum)).
                append($('<td>', {'class': 'new contents'})
                       .append(flatten(buildReplaceRegions(newRegion, newContent))));
        });
    }

    var operations = {
        'equal': buildEqualChunk,
        'insert': buildInsertChunk,
        'delete': buildDeleteChunk,
        'replace': buildReplaceChunk
    };

    function buildDiffTable(chunks, oldContents, newContents) {
        var $table = $('<table>', {'class': 'code'});

        $.each(chunks, function() {
            $table.append(flatten(operations[this.change](this, oldContents, newContents)));
        });

        return $table;
    };

    return { buildDiffTable: buildDiffTable };

});
