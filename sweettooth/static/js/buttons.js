"use strict";

define(['jquery', 'messages', 'dbus!_',
        'switch', 'jquery.tipsy'], function($, messages, dbusProxy) {
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
                var _state = ExtensionState.UNINSTALLED;
                if (extensions[uuid])
                    _state = extensions[uuid].state;

                elem.data({'elem': elem,
                           'state': _state});

                button.data('elem', elem);
                button.switchify();
                if (button.hasClass('insensitive'))
                    return;

                button.bind('changed', function(e, newValue) {
                    var oldState = elem.data('state');
                    if (newValue) {
                        if (oldState == ExtensionState.UNINSTALLED) {
                            // Extension is installed and we flick the switch on,
                            // install.
                            dbusProxy.InstallExtension(elem.data('manifest'));
                        } else if (oldState == ExtensionState.DISABLED) {
                            dbusProxy.EnableExtension(uuid);
                        }
                    } else {
                        if (oldState == ExtensionState.ENABLED)
                            dbusProxy.DisableExtension(uuid);
                    }
                });

                elem.bind('state-changed', function(e, newState) {
                    elem.data('state', newState);
                    button.switchify('insensitive', false);
                    button.tipsy({ gravity: 'e', fade: true });
                    if (newState == ExtensionState.DISABLED ||
                        newState == ExtensionState.UNINSTALLED) {
                        button.switchify('activate', false);
                    } else if (newState == ExtensionState.ENABLED) {
                        button.switchify('activate', true);
                    } else if (newState == ExtensionState.ERROR) {
                        button.switchify('insensitive', true);
                        button.attr('title', "This extension had an error");
                    } else if (newState == ExtensionState.OUT_OF_DATE) {
                        button.switchify('insensitive', true);
                        button.attr('title', "This extension is not compatible with your version of GNOME.");
                    }
                });
                elem.trigger('state-changed', _state);
                elems[uuid] = elem;
            });
        });
    };

});
