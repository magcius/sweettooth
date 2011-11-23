"use strict";

define(['jquery'], function($) {
    $.fn.uploadify = function(url) {
        var $elem = $(this), $input = $elem.find('input');
        if ($elem.data('uploader'))
            return;

        var BOUNDARY = ' -- 598275094719306587185414';
        // Stolen from http://demos.hacks.mozilla.org/openweb/imageUploader/js/extends/xhr.js
        function buildMultipart(filedata) {
            var body = '--' + BOUNDARY;

            body += '\r\nContent-Disposition: form-data; name=\"file\"';
            body += '; filename=\"file\"\r\nContent-type: image/png';
            body += '\r\n\r\n' + filedata + '\r\n--' + BOUNDARY;

            return body;
        }

        function upload(e) {
            function uploadComplete(result) {
                var $old = $elem.children().first();
                var $img = $('<img>', { 'src': result });
                $img.replaceAll($old);
                $elem.removeClass('placeholder');
            }

            var dt, file;
            if (e.originalEvent.dataTransfer)
                dt = e.originalEvent.dataTransfer;
            else
                dt = this;

            file = dt.files[0];

            if (!file)
                return false;

            if (window.FormData) {
                var fd = new FormData();
                fd.append('file', file);

                var df = $.ajax(url, { type: 'POST',
                                       // Let the XMLHttpRequest figure out the mimetype from the FormData
                                       // http://dev.w3.org/2006/webapi/XMLHttpRequest-2/Overview.html#the-send-method
                                       contentType: false,
                                       processData: false,
                                       data: fd });
                df.done(uploadComplete);
            } else {
                var filereader = new FileReader();
                filereader.onload = function(e) {
                    var url = e.target.result;
                    var df = $.ajax(url, { type: 'POST',
                                           contentType: 'multipart/form-data; boundary="' + BOUNDARY + '"',
                                           data: buildMultipart(url) });
                    df.done(uploadComplete);
                };
                filereader.readAsBinaryString(file);
            }

            return false;
        }

        var $drop = $('<span>', { 'class': 'drop' }).hide().appendTo($elem);

        var inClick = false;
        $elem.bind({
            click: function() {
                // Prevent the handler from running twice from bubbling.
                if (inClick)
                    return;

                inClick = true;
                $input[0].click();
                inClick = false;
                return false;
            },

            dragover: function() {
                // Have to prevent default action to define a drop target.
                return false;
            },

            dragenter: function(e) {
                if (e.relatedTarget == $elem[0])
                    $drop.fadeIn();

                return false;
            },

            dragleave: function(e) {
                if (e.relatedTarget == $elem[0])
                    $drop.fadeOut();

                return false;
            },

            drop: upload
        });

        $input.bind('change', upload);

        $elem.data('uploader', true);
    };
});
