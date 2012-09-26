// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['templates/templatedata', 'mustache'], function(templatedata, mustache) {
    "use strict";

    var exports = {};
    var cache = {};

    for (var prop in templatedata) {
        var value = templatedata[prop];
        cache[prop] = mustache.compilePartial(prop, value);
    }

    exports.get = function get(name) {
        return cache[name];
    }

    return exports;
});
