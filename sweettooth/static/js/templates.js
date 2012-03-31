"use strict";

define(['templates/templatedata', 'mustache'], function(templatedata) {

    var exports = {};
    var partials = exports._P = {};
    exports._T = templatedata;

    function compile(template) {
        // We have our own template caching, don't use Mustache's.
        var compiled = Mustache.compile(template, { cache: false });
        var wrapper = function(view) {
            return compiled(view, partials);
        };
        wrapper.compiled = true;
        return wrapper;
    }

    function _compileTemplateData(data, out, prefix) {
        for (var propname in data) {
            var v = data[propname], pkey;
            if (prefix)
                pkey = prefix + "." + propname;
            else
                pkey = propname;

            if (typeof(v) === typeof({})) {
                out[propname] = _compileTemplateData(v, {}, pkey);
            } else {
                out[propname] = partials[pkey] = compile(v);
            }
        }
        return out;
    }

    _compileTemplateData(templatedata, exports, "");
    return exports;
});
