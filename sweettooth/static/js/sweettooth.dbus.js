(function($) {

    var dbusProxy, testing;
    var available = SweetTooth.DBusProxyInterfaces.Available;
    for (var i = 0; i < available.length; i ++) {
        var iface = available[i];
        try {
            testing = new iface();
        } catch (e) {
            continue;
        }
        if (testing && testing.active) {
            dbusProxy = SweetTooth.DBusProxy = testing;
            break;
        }
    }

    var buttons = SweetTooth.Buttons = {};

    function _wrapDBusProxyMethod(meth) {
        return function(event) {
            meth.call(dbusProxy, event.data.config);
            buttons.GetCorrectButton(event.data.config);
            return false;
        };
    }

    buttons.InstallExtension = _wrapDBusProxyMethod(dbusProxy.InstallExtension);
    buttons.DisableExtension = _wrapDBusProxyMethod(dbusProxy.DisableExtension);
    buttons.EnableExtension  = _wrapDBusProxyMethod(dbusProxy.EnableExtension);

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
            dbusProxy.GetErrors(event.data.config.uuid).done(callback);

    };

    var states = buttons.States = {};
    var state = SweetTooth.ExtensionState;
    states[state.ENABLED]     = {"class": "disable", "content": "Disable",
                                 "handler": buttons.DisableExtension};

    states[state.DISABLED]    = {"class": "enable", "content": "Enable",
                                 "handler": buttons.EnableExtension};

    states[state.UNINSTALLED] = {"class": "install", "content": "Install",
                                 "handler": buttons.InstallExtension};

    states[state.ERROR]       = {"class": "error", "content": "Error",
                                 "handler": buttons.GetErrors};

    states[state.OUT_OF_DATE] = {"class": "ood", "content": "Out of Date"};

    states[state.DOWNLOADING] = {"class": "downloading", "content": "Downloading..."};

    buttons.ShowCorrectButton = function(config, stateid) {
        var buttonState = states[(!!stateid) ? stateid : state.UNINSTALLED];
        var button = config.button;
        button.html(buttonState.content);

        // 'class' is a reserved word in JS.
        button.removeClass().addClass('button').addClass(buttonState['class']);
        button.unbind('click');

        if (buttonState.handler)
            button.bind('click', {config: config}, buttonState.handler);
    };

    buttons.GetCorrectButton = function(config) {
        dbusProxy.GetExtensionInfo(config.uuid).done(function(meta) {
            buttons.ShowCorrectButton(config, meta.state);
        });
    };

    var configs = {};

    dbusProxy.extensionChangedHandler = function(uuid, newState, _) {
        buttons.ShowCorrectButton(configs[uuid], newState);
    };

    // Magical buttons.
    $.fn.buttonify = function() {
        var container = $(this);
        if (!dbusProxy.active) {
            container.find('.button').hide();
            return;
        }

        function callback(extensions) {
            container.each(function () {
                var element = $(this);
                var config = {"uuid": element.attr('data-uuid'),
                              "version": "latest", // XXX
                              "manifest": element.attr('data-manifest'),
                              "element": element,
                              "button": element.find('.button')};

                configs[config.uuid] = config;

                var meta = extensions[config.uuid] || {"state": state.UNINSTALLED};
                buttons.ShowCorrectButton(config, meta.state);
            });
        }

        dbusProxy.ListExtensions().done(callback);
    };

})(jQuery);
