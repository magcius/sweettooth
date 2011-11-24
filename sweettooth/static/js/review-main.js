"use strict";

require(['jquery', 'main', 'review'], function($) {
    $(document).ready(function() {
        $("#files").reviewify(false);
        $("#diff").reviewify(true);
    });
});
