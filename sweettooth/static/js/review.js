"use strict";

define(['jquery'], function($) {

    function createFileView(data) {
        var $fileView, $table, $tr;

        $tr = $('<tr>');
        $table = $('<table>').append($tr);

        if (data.num_lines) {
            var count = data.num_lines;
            var lines = [];
            lines.push("<td class=\"linenumbers\"><pre>");
            for (var i = 1; i < (count + 1); i ++) {
                lines.push("<span rel=\"L" + i + "\">" + i + "</span>\n");
            }
            lines.push("</pre></td>");

            $tr.append(lines.join(''));
        }

        $fileView = $('<div>', {'class': 'file'}).
            appendTo($('<td>', {'width': '100%'}).appendTo($tr));

        $fileView.html(data.html);

        return $table;
    }

    $.fn.reviewify = function() {
        var $elem = $(this);
        var $fileList = $('<ul>', {'class': 'filelist'}).appendTo($elem);
        var fileurl = $elem.data('fileurl');

        // Hide the file list until we're done grabbing all the elements.
        $fileList.hide();

        var $fileDisplay = $('<div>', {'class': 'filedisplay'}).appendTo($elem);
        $fileDisplay.css('position', 'relative');

        var $currentFile = null;

        var req = $.ajax({
            type: 'GET',
            dataType: 'json',
            url: fileurl
        });

        req.done(function(data) {
            $.each(data, function() {
                var data = this;
                var $selector = $('<a>', {'class': 'fileselector'}).text(data.filename);
                var $file = null;

                $selector.click(function() {
                    if ($selector.hasClass('selected'))
                        return;

                    if ($file === null)
                        $file = createFileView(data).hide().appendTo($fileDisplay);

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

                    $currentFile = $file;
                });

                $('<li>').append($selector).appendTo($fileList);
            });

            $fileList.show();

            // Select the first item.
            $fileList.find('li a.fileselector').first().click();
        });
    };
});
