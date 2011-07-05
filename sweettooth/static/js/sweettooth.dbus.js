(function($) {

    var dbusProxy = new SweetTooth.DBusProxy();
    if (!dbusProxy) {
        // We don't have a proper DBus proxy -- it's probably an old
        // version of GNOME3 or the Shell.
        SweetTooth.Messages.addError("You do not appear to have an up "+
                                     "to date version of GNOME3");

        // If we don't have a proper proxy interface, give us a simple
        // to prevent undefined errors in the code below.
        dbusProxy = SweetTooth.DBusProxy = { active: false };
    }

    var buttons = SweetTooth.Buttons = {};

    function _wrapDBusProxyMethod(meth, attr) {
        if (!meth)
            return;

        return function(event) {
            var elem = $(this).data('elem');
            meth.call(dbusProxy, elem.data(attr));
            return false;
        };
    }

    buttons.InstallExtension = _wrapDBusProxyMethod(dbusProxy.InstallExtension, 'manifest');
    buttons.DisableExtension = _wrapDBusProxyMethod(dbusProxy.DisableExtension, 'uuid');
    buttons.EnableExtension  = _wrapDBusProxyMethod(dbusProxy.EnableExtension, 'uuid');

    buttons.GetErrors = function(event) {
        var elem = $(this).data('elem');

        function callback(data) {
            var log = $('<div class="error-log"></div>');
            $.each(data, function(idx, error) {
                log.append($('<span class="line"></span>').text(error));
            });
            elem.append(log);
            log.hide().slideDown();
        }

        var eventLog = elem.find('.error-log');
        if (eventLog.length)
            eventLog.slideToggle();
        else
            dbusProxy.GetErrors(elem.data('uuid')).done(callback);
    };

    var states = {};
    var state = SweetTooth.ExtensionState;
    states[state.ENABLED]     = {'style': 'disable', 'content': "Disable",
                                 'handler': buttons.DisableExtension};

    states[state.DISABLED]    = {'style': 'enable', 'content': "Enable",
                                 'handler': buttons.EnableExtension};

    states[state.UNINSTALLED] = {'style': 'install', 'content': "Install",
                                 'handler': buttons.InstallExtension};

    states[state.ERROR]       = {'style': 'error', 'content': "Error",
                                 'handler': buttons.GetErrors};

    states[state.OUT_OF_DATE] = {'style': 'ood', 'content': "Out of Date"};

    states[state.DOWNLOADING] = {'style': 'downloading', 'content': "Downloading..."};

    $.fn.showCorrectButton = function(stateid) {
        var elem = $(this);
        var button = elem.find('.button');
        var buttonState = states[(!!stateid) ? stateid : state.UNINSTALLED];
        button.
            html(buttonState.content).
            removeClass().addClass('button').
            addClass(buttonState.style).unbind('click');

        if (buttonState.handler)
            button.bind('click', buttonState.handler);
    };

    $.fn.getCorrectButton = function() {
        var elem = $(this).data('elem');
        dbusProxy.GetExtensionInfo(elem.data('uuid')).done(function(meta) {
            elem.showCorrectButton(meta.state);
        });
    };

    // uuid => elem
    var elems = {};

    dbusProxy.extensionChangedHandler = function(uuid, newState, _) {
        elems[uuid].trigger('state-changed', newState);
    };

    $.fn.buttonify = function() {
        var container = $(this);

        if (!dbusProxy.active) {
            // Don't show our buttons -- CSS styles define a clickable
            // area even with no content.
            container.find('.button').hide();
            return;
        }

        dbusProxy.ListExtensions().done(function(extensions) {
            container.each(function () {
                var elem = $(this);
                var button = elem.find('.button');
                var uuid = elem.data('uuid');
                var meta = extensions[uuid] || {'state': state.UNINSTALLED};

                button.data('elem', elem);
                elem.data('elem', elem);
                elem.data('meta', meta);
                elem.data('state', meta.state);
                elem.bind('state-changed', function(e, newState) {
                    var elem = $(this);
                    var meta = elem.data('meta');
                    meta.state = newState;
                    return elem.showCorrectButton(newState);
                });
                elem.trigger('state-changed', meta.state);
                elems[uuid] = elem;
            });
        });
    };

})(jQuery);
