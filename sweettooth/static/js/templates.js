"use strict";

define(['templates/templatedata', 'mustache'], function(templatedata) {
    var module = {};
    module._T = templatedata;

    function compile(template) {
        // We have our own template caching, don't use Mustache's.
        return Mustache.compile(v, { cache: false });
    }

    function _compileTemplateData(data, out) {
        for (var propname in data) {
            var v = data[propname];
            if (typeof(v) === typeof({}))
                out[propname] = _compileTemplateData(v, {});
            else
                out[propname] = compile(v);
        }
        return out;
    }

    _compileTemplateData(templatedata, module);
    return module;
});
