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
            meth.call(dbusProxy, event.data.config.uuid);
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
    states[state.ENABLED]     = {"class": "disable", "text": "Disable",
                                 "handler": buttons.DisableExtension};

    states[state.DISABLED]    = {"class": "enable", "text": "Enable",
                                 "handler": buttons.EnableExtension};

    states[state.UNINSTALLED] = {"class": "install", "text": "Install",
                                 "handler": buttons.InstallExtension};

    states[state.ERROR]       = {"class": "error", "text": "Error",
                                 "handler": buttons.GetErrors};

    states[state.OUT_OF_DATE] = {"class": "ood", "text": "Out of Date"};

    buttons.ShowCorrectButton = function(config, stateid) {
        var buttonState = states[(!!stateid) ? stateid : state.UNINSTALLED];
        var button = config.button;
        button.text(buttonState.text);

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

    // Magical buttons.
    $.fn.buttonify = function() {
        if (!dbusProxy.active)
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

        dbusProxy.ListExtensions().done(callback);
    };

})(jQuery);
