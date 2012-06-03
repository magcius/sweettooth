// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery'], function($) {
    "use strict";

    $.fn.uploadify = function(url) {
        var $elem = $(this), $input = $elem.next('input');

        var BOUNDARY = ' -- 598275094719306587185414';
        // Stolen from http://demos.hacks.mozilla.org/openweb/imageUploader/js/extends/xhr.js
        function buildMultipart(filedata) {
            var body = '--' + BOUNDARY;

            body += '\r\nContent-Disposition: form-data; name=\"file\"';
            body += '; filename=\"file\"\r\nContent-type: image/png';
            body += '\r\n\r\n' + filedata + '\r\n--' + BOUNDARY;

            return body;
        }

        function uploadComplete(result) {
            var $old = $elem.children().first();
            var $img = $('<img>', { 'src': result });
            $img.replaceAll($old);
            $elem.removeClass('placeholder');
        }

        $input.on('change', function(e) {
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
        });

        $elem.on('click', function(e) {
            $input.get(0).click();
        });
    };
});
