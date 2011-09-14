"use strict";

define(['jquery', 'messages', 'dbus!_',
        'switch', 'jquery.tipsy'],
function($, messages, dbusProxy) {
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

        $.fn.addExtensionsSwitches = function() {
            // Don't show our switches -- CSS styles define a clickable
            // area even with no content.
            $(this).find('.switch').hide();
        };

        return {};
    }

    // This is stolen from the Shell:
    // http://git.gnome.org/browse/gnome-shell/tree/js/ui/extensionSystem.js
    function versionCheck(required, current) {
        var currentArray = current.split('.');
        var major = currentArray[0];
        var minor = currentArray[1];
        var point = currentArray[2];
        for (var i = 0; i < required.length; i++) {
            var requiredArray = required[i].split('.');
            if (requiredArray[0] == major &&
                requiredArray[1] == minor &&
                (requiredArray[2] == point ||
                 (requiredArray[2] == undefined && parseInt(minor) % 2 == 0)))
                return true;
        }
        return false;
    }

    // uuid => elem
    var elems = {};

    dbusProxy.extensionStateChangedHandler = function(uuid, newState, _) {
        elems[uuid].trigger('state-changed', newState);
    };

    function addExtensionSwitch(uuid, extension, $elem) {
        var shellVersions = $elem.data('sv');

        var $switch = $elem.find('.switch');
        var _state = ExtensionState.UNINSTALLED;

        if (shellVersions && !versionCheck(shellVersions, dbusProxy.ShellVersion)) {
            _state = ExtensionState.OUT_OF_DATE;
        } else if (extension) {
            _state = extension.state;
        }

        $elem.data({'elem': $elem,
                    'state': _state,
                    'uninstalled': false});

        $switch.data('elem', $elem);
        $switch.switchify();
        if ($switch.hasClass('insensitive'))
            return;

        $switch.bind('changed', function(e, newValue) {
            var oldState = $elem.data('state');
            if (newValue) {
                if (oldState == ExtensionState.UNINSTALLED) {
                    // If the extension is uninstalled and we
                    // flick the switch on, install.
                    dbusProxy.InstallExtension(uuid, $elem.data('pk').toString());
                } else if (oldState == ExtensionState.DISABLED) {
                    dbusProxy.EnableExtension(uuid);
                }
            } else {
                if (oldState == ExtensionState.ENABLED)
                    dbusProxy.DisableExtension(uuid);
            }
        });

        $elem.bind('state-changed', function(e, newState) {
            $elem.data('state', newState);
            $switch.switchify('insensitive', false);
            $switch.tipsy({ gravity: 'e', fade: true });
            if (newState == ExtensionState.DISABLED ||
                newState == ExtensionState.UNINSTALLED) {
                $switch.switchify('activate', false);
            } else if (newState == ExtensionState.ENABLED) {
                $switch.switchify('activate', true);
            } else if (newState == ExtensionState.ERROR) {
                $switch.switchify('insensitive', true);
                $switch.attr('title', "This extension had an error.");
            } else if (newState == ExtensionState.OUT_OF_DATE) {
                $switch.switchify('insensitive', true);
                messages.addError("This extension is not compatible with your version of GNOME.");
            }

            if ($elem.data('uninstalled') && (newState == ExtensionState.ENABLED ||
                                              newState == ExtensionState.ERROR ||
                                              newState == ExtensionState.OUT_OF_DATE)) {
                $elem.fadeIn({ queue: false }).slideDown();
                $elem.data('uninstalled', false);
            }

        });
        $elem.trigger('state-changed', _state);
        elems[uuid] = $elem;
    }

    $.fn.addLocalExtensions = function () {
        var $container = $(this);
        dbusProxy.ListExtensions().done(function(extensions) {
            $.each(extensions, function(uuid, extension) {
                function reinstall() {
                    dbusProxy.InstallExtension(uuid, $elem.data('pk').toString());

                    // If the user clicks "Install" we need to show that we
                    // installed it by reattaching the element, but we can't do
                    // that here -- the user might click "Cancel".
                    $elem.data('uninstalled', true);

                    message.slideUp();
                }

                function uninstall() {
                    dbusProxy.UninstallExtension(uuid).done(function(result) {
                        if (result) {
                            $elem.fadeOut({ queue: false }).slideUp({ queue: false });

                            // Construct a dummy <p> node as we need something
                            // to stuff everything else in...
                            var messageHTML = $("<p>You uninstalled </p>").
                                append($('<b>').text(extension.name)).
                                append(". ").
                                append($('<a>', {'href': '#'}).text("Undo?")).html();

                            var message = messages.addInfo(messageHTML);
                            message.find('a').click(reinstall);
                            $elem.data('undo-uninstall-message', message);
                        }
                    });
                }

                var $elem = $('<div>', {'class': 'extension'}).
                    append($('<div>', {'class': 'switch'})).
                    append($('<img>', {'class': 'icon'})).
                    append($('<h3>').text(extension.name)).
                    append($('<span>', {'class': 'author'})).
                    append($('<p>', {'class': 'description'}).text(extension.description));

                $.ajax({
                    url: "/ajax/d/",
                    dataType: "json",
                    data: { uuid: uuid },
                    type: "GET",
                }).done(function(result) {
                    $elem.
                        find('span.author').html(" by <a href=\"/accounts/profile/"+result.creator+"\">"+result.creator+"</a>").end().
                        find('h3').html($('<a>', {'href': result.link}).text(extension.name)).end().
                        find('img.icon').attr('src', result.icon).end().
                        append($('<button>', {'class': 'uninstall'}).text("Uninstall").bind('click', uninstall)).
                        data('pk', result.pk);
                });

                // The DOM element's CSS styles won't be fully
                // computed, so the switch will be incorrectly
                // positioned -- wait a bit before adding them.
                setTimeout(function() {
                    addExtensionSwitch(uuid, extension, $elem);
                }, 0);

                $container.append($elem);
            });
        });
    };

    $.fn.addExtensionsSwitches = function () {
        var $container = $(this);
        dbusProxy.ListExtensions().done(function(extensions) {
            $container.each(function () {
                var uuid = $(this).data('uuid');
                addExtensionSwitch(uuid, extensions[uuid], $(this));
            });
        });
    };

});
