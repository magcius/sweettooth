(function($) {

    var SweetTooth = window.SweetTooth = {};
    var state = SweetTooth.State = {
        // These constants should be kept in sync
        // with those in gnome-shell: see js/ui/extensionSystem.js
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4,

        // Not a real state, used when there's no extension
        // with the associated UUID in the extension map.
        UNINSTALLED: 99
    };

    var HOST = "http://localhost:16269/";
    var http = SweetTooth.LocalHTTP = { hasLocal: false };

    // Detect if the local system is up.
    $.ajax({ url: HOST + "ping",
             async: false,
             cache: false,
             success: function() { http.hasLocal = true; }});

    $(document).ajaxError(function(event, xhr, settings, exc) {
        if (!window.console || !window.console.error)
            return;

        window.console.error("AJAX: " + " in " + settings.url + "\n"
                             + xhr.responseText + " " + exc);
    });

    http.ListExtensions = function() {
        return $.ajax({ url: HOST + "list",
                        dataType: "json",
                        cache: false });
    };

    http.GetExtensionInfo = function(uuid) {
        return $.ajax({ url: HOST + "info",
                        dataType: "json",
                        data: {uuid: uuid},
                        cache: false });
    };

    http.GetErrors = function(uuid) {
        return $.ajax({ url: HOST + "errors",
                        dataType: "json",
                        data: {uuid: uuid},
                        cache: false });
    };

    http.InstallExtension = function(uuid) {
        // XXX for demo -- need real manifest
        var MANIFEST_BASE = "http://extensions.gnome.org/browse/manifest/";
        var url = MANIFEST_BASE + encodeURIComponent(uuid) + ".json";

        $.ajax({ url: HOST + "install",
                 cache: false,
                 data: {url: url} });
    };

    http.DoExtensionCommand = function(command, arg) {
        $.ajax({ url: HOST + "command/" + command,
                 cache: false,
                 data: {arg: arg} });
    };

    var buttons = SweetTooth.Buttons = {};

    buttons.InstallExtension = function(event) {
        http.InstallExtension(event.data.config.uuid);
        buttons.GetCorrectButton(event.data.config);
        return false;
    };

    buttons.DoExtensionCommand = function(event) {
        http.DoExtensionCommand(event.data.cmd, event.data.config.uuid);
        buttons.GetCorrectButton(event.data.config);
        return false;
    };

    buttons.GetErrors = function(event) {
        var elem = event.data.config.element;

        function callback(data) {
            var log = $('<div class="error-log"></div>');
            $.each(data, function(idx, error) {
                log.append($('<span class="line"></span>').text(error));
            });
            event.data.config.element.append(log);
            log.hide().slideDown();
        }

        var eventLog = elem.find('.error-log');
        if (eventLog.length)
            eventLog.slideToggle();
        else
            http.GetErrors(event.data.config.uuid).done(callback);

    };

    var states = buttons.States = {};
    states[state.ENABLED]     = {"class": "disable", "text": "Disable",
                                 "handler": {"func": buttons.DoExtensionCommand,
                                             "data": {"cmd": "disable"}}};

    states[state.DISABLED]    = {"class": "enable", "text": "Enable",
                                 "handler": {"func": buttons.DoExtensionCommand,
                                             "data": {"cmd": "enable"}}};

    states[state.UNINSTALLED] = {"class": "install", "text": "Install",
                                 "handler": {"func": buttons.InstallExtension}};

    states[state.ERROR]       = {"class": "error", "text": "Error",
                                 "handler": {"func": buttons.GetErrors}};

    states[state.OUT_OF_DATE] = {"class": "ood", "text": "Out of Date"};

    buttons.ShowCorrectButton = function(config, stateid) {
        var buttonState = states[(!!stateid) ? stateid : state.UNINSTALLED];
        var button = config.button;
        button.text(buttonState.text);

        // 'class' is a reserved word in JS.
        button.removeClass().addClass('button').addClass(buttonState['class']);
        button.unbind('click');

        if (buttonState.handler) {
            var handlerData = $.extend({config: config}, (buttonState.handler.data || {}));
            button.bind('click', handlerData, buttonState.handler.func);
        }
    };

    buttons.GetCorrectButton = function(config) {
        http.GetExtensionInfo(config.uuid).done(function(meta) {
            buttons.ShowCorrectButton(config, meta.state);
        });
    };

    // Magical buttons.
    $.fn.buttonify = function() {
        if (!http.hasLocal)
            return;

        var container = $(this);

        function callback(extensions) {
            container.each(function () {
                var element = $(this);
                var config = {"uuid": element.attr('data-uuid'),
                              "manifest": element.attr('data-manifest')};

                config.element = element;
                config.button = element.find('.button');

                var meta = extensions[config.uuid] || {"state": state.UNINSTALLED};
                buttons.ShowCorrectButton(config, meta.state);
            });
        }

        http.ListExtensions().done(callback);
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
