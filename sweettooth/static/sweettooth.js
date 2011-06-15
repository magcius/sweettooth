(function($) {

    var SweetTooth = {};
    var state = SweetTooth.State = {
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4
    };

    var HOST = "http://localhost:16269/";
    var http = SweetTooth.LocalHTTP = { hasLocal: false };

    $.ajax({ url: HOST,
             async: false,
             cache: false,
             success: function() { http.hasLocal = true; }});

    http.GetExtensions = function(callback, errback) {
        $.ajax({ url: HOST + "list",
                 dataType: "json",
                 cache: false,
                 success: callback,
                 error: errback });
    }

    http.InstallExtension = function(manifest) {
        $.ajax({ url: HOST + "install",
                 cache: false,
                 data: {url: manifest} });
    };

    http.DoExtensionCommand = function(command, arg) {
        $.ajax({ url: HOST + "command/" + command,
                 cache: false,
                 data: {arg: arg} });
    };

    var buttons = SweetTooth.buttons = {};

    buttons.ShowCorrectButtons = function(config) {

        function callback(extensions) {
            config.install.hide();
            config.disable.hide();
            config.enable.hide();

            var meta = extensions[config.uuid];
            if (meta) {
                if (meta.state == state.ENABLED)
                    config.disable.show();
                else if (meta.state == state.DISABLED)
                    config.enable.show();
            } else {
                config.install.show();
            }
        }

        function errback() {
            config.install.show();
            config.disable.show();
            config.enable.show();
        }

        http.GetExtensions(callback, errback);
    };

    buttons.InstallExtension = function(event) {
        http.InstallExtension(event.data.config.manifest);
        buttons.ShowCorrectButtons(event.data.config);
        return false;
    };

    buttons.DoExtensionCommand = function(event) {
        http.DoExtensionCommand(event.data.cmd, event.data.config.uuid);
        buttons.ShowCorrectButtons(event.data.config);
        return false;
    };

    // Magical buttons.
    $.fn.buttonify = function(CONFIG) {
        if (!http.hasLocal)
            return;

        var element = $(this);
        var config = $.extend({}, CONFIG);
        element.data('_sweettooth_config', config);

        var i = config.install = element.find(".button.install");
        var d = config.disable = element.find(".button.disable");
        var e = config.enable = element.find(".button.enable");

        i.bind('click', {config: config}, buttons.InstallExtension);
        d.bind('click', {config: config, cmd: 'disable'}, buttons.DoExtensionCommand);
        e.bind('click', {config: config, cmd: 'enable'}, buttons.DoExtensionCommand);

        buttons.ShowCorrectButtons(config);
    };

    $(document).ready(function() {

        $("#login_link").click(function(event) {
            $(this).toggleClass("selected");
            $("#login_popup_form").slideToggle();
            event.preventDefault();
            return false;
        });

    });

})(jQuery);