// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'main', 'review'], function($) {
    "use strict";

    $(document).ready(function() {
        $("#files").reviewify(false);
        $("#diff").reviewify(true);
    });
});
