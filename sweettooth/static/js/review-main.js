"use strict";

define(['jquery', 'main', 'review'], function($) {
    $(document).ready(function() {
        $("#files").reviewify(false);
        $("#diff").reviewify(true);
    });
});
