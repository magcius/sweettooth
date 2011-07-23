define(['jquery', '_DBUS_PLG'], function($, pluginObject) {
    function _makePromise(result) {
        // Make a new completed promise -- when we move the plugin
        // over to async, we can remove this.
        return (new $.Deferred()).resolve($.parseJSON(result));
    }

    var proxy = {
        ListExtensions: function() {
            return _makePromise(pluginObject.listExtensions());
        },

        GetExtensionInfo: function(uuid) {
            return _makePromise(pluginObject.getExtensionInfo(uuid));
        },

        GetErrors: function(uuid) {
            return _makePromise(pluginObject.getExtensionErrors(uuid));
        },

        EnableExtension: function(uuid) {
            pluginObject.setExtensionEnabled(uuid, true);
        },

        DisableExtension: function(uuid) {
            pluginObject.setExtensionEnabled(uuid, false);
        },

        InstallExtension: function(manifest) {
            pluginObject.installExtension(manifest);
        },

        extensionStateChangedHandler: null
    };

    pluginObject.onchange = function(uuid, newState, error) {
        try {
            proxy.extensionStateChangedHandler(uuid, newState, error);
        } catch(e) {
            // There's no way to tell if a property is callable, so
            // just catch the error.
        }
    };

    return proxy;
});
