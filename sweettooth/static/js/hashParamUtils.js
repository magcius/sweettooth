// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(["jquery"], function($) {
    "use strict";

    var exports = {};

    exports.getHashParams = function getHashParams() {
        var hash = window.location.hash;
        if (!hash)
            return {};

        var values = hash.slice(1).split('&');
        var obj = {};
        for (var i = 0; i < values.length; i++) {
            if (!values[i])
                continue;

            var kv = values[i].split('=');
            var key = kv[0], value = kv[1];
            if (key in obj && $.isArray(obj[key]))
                obj[key].push(value);
            else if (key in obj)
                obj[key] = [obj[key], value];
            else
                obj[key] = value;
        }

        return obj;
    };

    exports.setHashParams = function setHashParams(obj) {
        window.location.hash = $.param(obj);
    };

    exports.setHashParam = function setHashParam(name, value) {
        var hp = getHashParams();
        if (value === undefined)
            delete hp[name];
        else
            hp[name] = value;
        setHashParams(hp);
    };

    return exports;
});
