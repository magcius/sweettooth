"use strict";

define([], function() {

    var module = {};

    // ExtensionState and versionCheck are stolen and should
    // be kept in sync those from the Shell.
    // Licensed under GPL2+
    // See: http://git.gnome.org/browse/gnome-shell/tree/js/ui/extensionSystem.js

    module.ExtensionState = {
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4,
        DOWNLOADING: 5,
        INITIALIZED: 6,

        // Not a real state, used when there's no extension
        // with the associated UUID in the extension map.
        UNINSTALLED: 99
    };

    module.versionCheck = function(required, current) {
        var currentArray = current.split('.');
        var major = currentArray[0];
        var minor = currentArray[1];
        var point = currentArray[2];
        for (var i = 0; i < required.length; i++) {
            var requiredArray = required[i].split('.');
            if (requiredArray[0] == major &&
                requiredArray[1] == minor &&
                (requiredArray[2] == point ||
                 (requiredArray[2] == undefined && parseInt(minor) % 2 == 0)))
                return true;
        }
        return false;
    };

    return module;

});
