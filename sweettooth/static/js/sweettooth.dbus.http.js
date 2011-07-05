(function($) {
    var iface = SweetTooth.DBusProxyInterfaces.LocalHTTP = function() {
        this._init();
    };

    SweetTooth.DBusProxyInterfaces.LocalHTTP.prototype = {
        HOST: "http://localhost:16269/",

        _init: function() {
            this.active = false;

            // Detect if the local system is up.
            $.ajax({ url: this.HOST + "ping",
                     async: false,
                     cache: false,
                     context: this,
                     success: function() { this.active = true; }});

            $(document).ajaxError(function(event, xhr, settings, exc) {
                if (!window.console || !window.console.error)
                    return;

                window.console.error("AJAX: " + " in " + settings.url + "\n"
                                     + xhr.responseText + " " + exc);
            });
        },

        ListExtensions: function() {
            return $.ajax({ url: this.HOST + "list",
                            dataType: "json",
                            cache: false });
        },

        GetExtensionInfo: function(uuid) {
            return $.ajax({ url: this.HOST + "info",
                            dataType: "json",
                            data: {uuid: uuid},
                            cache: false });
        },

        GetErrors: function(uuid) {
            return $.ajax({ url: this.HOST + "errors",
                            dataType: "json",
                            data: {uuid: uuid},
                            cache: false });
        },

        EnableExtension: function(uuid) {
            $.ajax({ url: this.HOST + "enable",
                     cache: false,
                     data: {uuid: uuid} });
        },

        DisableExtension: function(uuid) {
            $.ajax({ url: this.HOST + "disable",
                     cache: false,
                     data: {uuid: uuid} });
        },

        InstallExtension: function(manifest) {
            $.ajax({ url: this.HOST + "install",
                     cache: false,
                     data: {url: manifest} });
        }
    };

    SweetTooth.DBusProxyInterfaces.Available.push(iface);
})(jQuery);
