// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['templates/templatedata', 'mustache'], function(templatedata, mustache) {
    "use strict";

    var exports = {};
    var cache = {};

    function _processPartials(prefix, data) {
        for (var prop in data) {
            var value = data[prop];
            var name;

            if (prefix)
                name = prefix + "/" + prop;
            else
                name = prop;

            if (typeof(value) === typeof({})) {
                // Subdirectory. Recurse.
                _processPartials(name, value);
            } else {
                // Template. Mustache will cache all partials for us.
                cache[name] = mustache.compilePartial(name, value);
            }
        }
    }
    _processPartials("", templatedata);

    exports.get = function get(name) {
        return cache[name];
    }

    return exports;
});
