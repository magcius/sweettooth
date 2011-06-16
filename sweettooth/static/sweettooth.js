(function($) {

    var SweetTooth = {};
    var state = SweetTooth.State = {
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4,
        UNINSTALLED: 5 // Dummy state.
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

    buttons.InstallExtension = function(event) {
        http.InstallExtension(event.data.config.manifest);
        buttons.ShowCorrectButton(event.data.config);
        return false;
    };

    buttons.DoExtensionCommand = function(event) {
        http.DoExtensionCommand(event.data.cmd, event.data.config.uuid);
        buttons.ShowCorrectButton(event.data.config);
        return false;
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

    states[state.ERROR]       = {"class": "error", "text": "Error"};
    states[state.OUT_OF_DATE] = {"class": "ood", "text": "Out of Date"};

    buttons.ShowCorrectButton = function(config) {
        function callback(extensions) {
            var meta = extensions[config.uuid];
            var buttonState = states[(!!meta) ? meta.state : state.UNINSTALLED];
            var button = config.button;
            button.text(buttonState.text);
            button.removeClass().addClass('button').addClass(buttonState['class']);
            button.unbind('click');
            console.log(buttonState, button);

            if (buttonState.handler) {
                var handlerData = $.extend({config: config}, (buttonState.handler.data || {}));
                button.bind('click', handlerData, buttonState.handler.func);
            }
        }

        function errback() {
            console.log(arguments);
        }

        console.log("BBB", config.uuid);

        http.GetExtensions(callback, errback);
    };

    // Magical buttons.
    $.fn.buttonify = function() {
        if (!http.hasLocal)
            return;

        $(this).each(function () {
            var element = $(this);
            var config = {"uuid": element.attr('data-uuid'),
                          "manifest": element.attr('data-manifest')};

            config.button = element.find('.button');
            console.log(config.uuid);
            buttons.ShowCorrectButton(config);
        });
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