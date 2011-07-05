(function($) {
    var iface = SweetTooth.DBusProxy = function() {
        this._init();
    };

    SweetTooth.DBusProxy.prototype = {
        MIME_TYPE: 'application/x-gnome-shell-integration',

        _init: function() {
            this.active = false;
            this.pluginObject = document.createElement('embed');
            $(this.pluginObject).attr('type', this.MIME_TYPE);

            // Netscape plugins are strange: if you make them invisible with
            // CSS or give them 0 width/height, they won't load. Just smack it
            // off-screen so it isn't visible, but still works.
            $(this.pluginObject).css({ position: 'absolute',
                                       left: '-1000em',
                                       top: '-1000em' });
            $(document.body).append(this.pluginObject);

            this.apiVersion = this.pluginObject.apiVersion;
            if (!this.apiVersion)
                return;

            this.active = true;

            this.shellVersion = this.pluginObject.shellVersion;

            var me = this;
            this.pluginObject.onchange = function(uuid, newState, error) {
                me._extensionStateChanged.call(me, uuid, newState, error);
            };

            this.extensionChangedHandler = null;
        },

        _extensionStateChanged: function(uuid, newState, error) {
            if (this.extensionChangedHandler)
                this.extensionChangedHandler(uuid, newState, error);
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

        EnableExtension: function(uuid) {
            this.pluginObject.setExtensionEnabled(uuid, true);
        },

        DisableExtension: function(uuid) {
            this.pluginObject.setExtensionEnabled(uuid, false);
        },

        InstallExtension: function(manifest) {
            this.pluginObject.installExtension(manifest);
        }
    };
})(jQuery);
