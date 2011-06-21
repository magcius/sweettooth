(function($) {

    var SweetTooth = window.SweetTooth = {};
    var state = SweetTooth.State = {
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4,
        UNINSTALLED: 5 // Dummy state.
    };

    var HOST = "http://localhost:16269/";
    var http = SweetTooth.LocalHTTP = { hasLocal: false };

    $(document).ajaxError(function(_, __, ___, exc) {
        if (window.console && window.console.error)
            window.console.error("AJAX: " + exc);
    });

    $.ajax({ url: HOST,
             async: false,
             cache: false,
             success: function() { http.hasLocal = true; }});

    http.ListExtensions = function() {
        return $.ajax({ url: HOST + "list",
                        dataType: "json",
                        cache: false });
    };

    http.GetExtensionInfo = function() {
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
        buttons.ShowCorrectButton(event.data.config);
        return false;
    };

    buttons.DoExtensionCommand = function(event) {
        http.DoExtensionCommand(event.data.cmd, event.data.config.uuid);
        buttons.ShowCorrectButton(event.data.config);
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

    buttons.ShowCorrectButton = function(config, stateName) {
        var buttonState = states[(!!stateName) ? stateName : state.UNINSTALLED];
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

    buttons.GetCorrectButton = function(uuid) {
        function callback(extensions) {
            var meta = extensions[config.uuid];
            buttons.ShowCorrectButton(meta.state);
        }

        http.GetExtensionMeta(uuid).done(callback);
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
                buttons.ShowCorrectButton(config, extensions[config.uuid].state);
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
