// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['templates/templatedata', 'mustache'], function(templatedata, mustache) {
    "use strict";

    var exports = {};
    exports._T = templatedata;

    function _compileTemplateData(data, out, prefix) {
        for (var propname in data) {
            var v = data[propname], pkey;
            if (prefix)
                pkey = prefix + "." + propname;
            else
                pkey = propname;

            if (typeof(v) === typeof({})) {
                // Subdirectory. Recurse.
                out[propname] = _compileTemplateData(v, {}, pkey);
            } else {
                // Template. Mustache will cache all partials for us.
                out[propname] = mustache.compilePartial(pkey, v);
            }
        }
        return out;
    }

    _compileTemplateData(templatedata, exports, "");
    return exports;
});
