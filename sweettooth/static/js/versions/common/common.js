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

        LaunchExtensionPrefs: function(uuid) {
            return API.launchExtensionPrefs(uuid);
        },

        LaunchExtensionPrefsDummy: function(uuid) { },

        EnableExtension: function(uuid) {
            API.setExtensionEnabled(uuid, true);
        },

        DisableExtension: function(uuid) {
            API.setExtensionEnabled(uuid, false);
        },

        InstallExtensionOne: function(uuid) {
            API.installExtension(uuid);
        },

        InstallExtensionTwo: function(uuid) {
            API.installExtension(uuid, -1);
        },

        UninstallExtension: function(uuid) {
            return _makePromise(API.uninstallExtension(uuid));
        },

        API_onchange: function(proxy) {
            return function(uuid, newState, error) {
                if (proxy.extensionStateChangedHandler !== null)
                    proxy.extensionStateChangedHandler(uuid, newState, error);
            };
        },

        API_onshellrestart: function(proxy) {
            return function() {
                if (proxy.shellRestartHandler !== null)
                    proxy.shellRestartHandler();
            };
        }
    };
});
