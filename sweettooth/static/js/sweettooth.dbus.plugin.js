(function($) {
    var iface = SweetTooth.DBusProxyInterfaces.LocalPlugin = function() {
        this._init();
    };

    SweetTooth.DBusProxyInterfaces.LocalPlugin.prototype = {
        MIME_TYPE: "application/x-gnome-shell-integration",

        _init: function() {
            this.active = false;
            this.pluginObject = document.createElement('embed');
            this.pluginObject.setAttribute('type', this.MIME_TYPE);
            $(this.pluginObject).css({ position: "absolute",
                                       left: "-1000em", 
                                       top: "-1000em" });
            $(document.body).append(this.pluginObject);

            this.API_VERSION = this.pluginObject.apiVersion;
            if (!!this.API_VERSION)
                this.active = true;

            var me = this;
            this.pluginObject.onchange = function(uuid, newState, error) {
                return me._extensionStateChanged.call(me, uuid, newState, error);
            };

            this.extensionChangedHandler = null;
        },

        _extensionStateChanged: function(uuid, newState, error) {
            if (!!this.extensionChangedHandler)
                return this.extensionChangedHandler(uuid, newState, error);
        },

        _makePromise: function(result) {
            // Make a new completed promise -- when we move the plugin
            // over to async, we can remove this.
            return (new $.Deferred()).resolve($.parseJSON(result));
        },

        ListExtensions: function() {
            return this._makePromise(this.pluginObject.listExtensions());
        },

        GetExtensionInfo: function(uuid) {
            return this._makePromise(this.pluginObject.getExtensionInfo(uuid));
        },

        GetErrors: function(uuid) {
            return this._makePromise(this.pluginObject.getExtensionErrors(uuid));
        },

        EnableExtension: function(config) {
            this.pluginObject.setExtensionEnabled(config.uuid, true);
        },

        DisableExtension: function(config) {
            this.pluginObject.setExtensionEnabled(config.uuid, false);
        },

        InstallExtension: function(config) {
            this.pluginObject.installExtension(config.manifest);
        }
    };

    SweetTooth.DBusProxyInterfaces.Available.push(iface);
})(jQuery);
