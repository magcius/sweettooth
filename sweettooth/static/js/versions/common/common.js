"use strict";

define(['jquery', 'dbus!API'], function($, API) {
    function _makePromise(result) {
        // Make a new completed promise -- when we move the plugin
        // over to async, we can remove this.
        return (new $.Deferred()).resolve($.parseJSON(result));
    }

    return {
        _makePromise: _makePromise,

        ListExtensions: function() {
            return _makePromise(API.listExtensions());
        },

        GetExtensionInfo: function(uuid) {
            return _makePromise(API.getExtensionInfo(uuid));
        },

        GetErrors: function(uuid) {
            return _makePromise(API.getExtensionErrors(uuid));
        },

        EnableExtension: function(uuid) {
            API.setExtensionEnabled(uuid, true);
        },

        DisableExtension: function(uuid) {
            API.setExtensionEnabled(uuid, false);
        },

        InstallExtension: function(uuid, server_uuid) {
            API.installExtension(uuid, server_uuid);
        },

        UninstallExtension: function(uuid) {
            return _makePromise(API.uninstallExtension(uuid));
        },

        API_onchange: function(proxy) {
            return function(uuid, newState, error) {
                try {
                    proxy.extensionStateChangedHandler(uuid, newState, error);
                } catch(e) {
                    // There's no way to tell if a property is callable, so
                    // just catch the error.
                }
            };
        },

        API_onshellrestart: function(proxy) {
            return function() {
                try {
                    proxy.shellRestartHandler();
                } catch(e) {
                    // There's no way to tell if a property is callable, so
                    // just catch the error.
                }
            };
        }
    };
});
