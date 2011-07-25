"use strict";

define(['jquery', 'messages', 'dbus!_'], function($, messages, dbusProxy) {
    var ExtensionState = {
        // These constants should be kept in sync
        // with those in gnome-shell: see js/ui/extensionSystem.js
        ENABLED: 1,
        DISABLED: 2,
        ERROR: 3,
        OUT_OF_DATE: 4,
        DOWNLOADING: 5,

        // Not a real state, used when there's no extension
        // with the associated UUID in the extension map.
        UNINSTALLED: 99
    };

    if (!dbusProxy) {
        // We don't have a proper DBus proxy -- it's probably an old
        // version of GNOME3 or the Shell.
        messages.addError("You do not appear to have an up " +
                          "to date version of GNOME3");

        $.fn.buttonify = function() {
            // Don't show our buttons -- CSS styles define a clickable
            // area even with no content.
            $(this).find('.button').hide();
        };

        return {};
    }

    var buttons = {};

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
    var state = ExtensionState;
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

    // uuid => elem
    var elems = {};

    dbusProxy.extensionStateChangedHandler = function(uuid, newState, _) {
        elems[uuid].trigger('state-changed', newState);
    };

    $.fn.buttonify = function () {
        var $container = $(this);
        dbusProxy.ListExtensions().done(function(extensions) {
            $container.each(function () {
                var elem = $(this);
                var button = elem.find('.button');
                var uuid = elem.data('uuid');
                var state = ExtensionState.UNINSTALLED;
                if (extensions[uuid])
                    state = extensions[uuid].state;

                button.data('elem', elem);
                elem.data('elem', elem);
                elem.data('state', state);
                elem.bind('state-changed', function(e, newState) {
                    var button = elem.find('.button');
                    var buttonState = states[newState];
                    button.
                        html(buttonState.content).
                        removeClass().addClass('button').
                        addClass(buttonState.style).unbind('click');

                    if (buttonState.handler)
                        button.bind('click', buttonState.handler);
                });
                elem.trigger('state-changed', state);
                elems[uuid] = elem;
            });
        });
    };

});
