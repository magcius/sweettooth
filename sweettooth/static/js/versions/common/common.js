// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'dbus!API'], function($, API) {
    "use strict";

    function _makeRawPromise(result) {
        // Make a new completed promise -- when we move the plugin
        // over to async, we can remove this.
        return (new $.Deferred()).resolve(result);
    }

    function _makePromise(result) {
        return _makeRawPromise(JSON.parse(result));
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
            return _makeRawPromise('succeeded');
        },

        InstallExtensionTwo: function(uuid) {
            API.installExtension(uuid, "");
            return _makeRawPromise('succeeded');
        },

        InstallExtensionAsync: function(uuid) {
            var d = new $.Deferred();
            API.installExtension(uuid, d.done.bind(d), d.fail.bind(d));
            return d;
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
