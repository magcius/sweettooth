// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'messages', 'dbus!_', 'extensionUtils', 'templates',
        'paginator', 'switch'],
function($, messages, dbusProxy, extensionUtils, templates) {
    "use strict";

    var ExtensionState = extensionUtils.ExtensionState;

    $.fn.buildShellVersionsInfo = function () {
        return this.each(function() {
            var $table = $(this);
            var $tbody = $table.find('tbody');
            var $extension = $table.parents('.extension');
            var urlBase = $extension.data('ver-url-base');

            $tbody.children().remove();

            var svm = $extension.data('svm');
            for (var version in svm) {
                if (!svm.hasOwnProperty(version))
                    continue;

                var vpk = extensionUtils.grabProperExtensionVersion(svm, version);

                var $tr = $('<tr>').appendTo($tbody);

                $('<td>').append($('<code>').text(version)).appendTo($tr);
                $('<td>').append($('<a>', {'href': urlBase + vpk.pk}).text(vpk.version)).appendTo($tr);
            }
        });
    };

    // While technically we shouldn't have mismatched API versions,
    // the plugin doesn't check whether the Shell matches, so if someone
    // is running with an old Shell version but a newer plugin, error out.
    if (dbusProxy.IsDummy) {
        // We don't have a proper DBus proxy -- it's probably an old
        // version of GNOME3 or the Shell.
        messages.addError(templates.messages.dummy_proxy());

        $.fn.addExtensionSwitch = function() {
            // Don't show our switches -- CSS styles define a clickable
            // area even with no content.
            return this.find('.switch').hide();
        };

        $.fn.addLocalExtensions = function() {
            return this.append(templates.messages.cannot_list_local());
        };

        $.fn.fillInErrors = function() {
            var $textarea = this.find('textarea[name=error]');
            var $hidden = this.find('input:hidden[name=has_errors]');
            $textarea.text(templates.messages.cannot_list_errors()).
                addClass('no-errors').attr('disabled', 'disabled');
            $hidden.val('');
            return this;
        };

        $.fn.grayOutIfOutOfDate = function() {
            return this;
        };

        return;
    }

    // uuid => elem
    var elems = {};

    dbusProxy.extensionStateChangedHandler = function(uuid, newState, _) {
        if (elems[uuid] !== undefined)
            elems[uuid].trigger('state-changed', newState);
    };

    dbusProxy.shellRestartHandler = function() {
        dbusProxy.ListExtensions().done(function(extensions) {
            $.each(extensions, function(meta) {
                if (elems[uuid] !== undefined)
                    elems[uuid].trigger('state-changed', meta.state);
            });
        });
    };

    function addExtensionSwitch(uuid, $elem, meta) {
        var $switch = $elem.find('.switch');
        var _state;
        if (meta && meta.state)
            _state = meta.state;
        else
            _state = ExtensionState.UNINSTALLED;

        $elem.find('.configure-button').on('click', function() {
            dbusProxy.LaunchExtensionPrefs(uuid);
        });

        $elem.data({'elem': $elem,
                    'state': _state,
                    'uninstalled': false,
                    'undo-uninstall-message': null});

        $switch.data('elem', $elem);
        $switch.switchify();

        function sendPopularity(action) {
            $.ajax({ url: '/ajax/adjust-popularity/',
                     type: 'POST',
                     data: { uuid: uuid,
                             action: action } });
        }

        function upgradeExtension() {
            $switch.switchify('customize').off('button-changed', upgradeExtension);
            dbusProxy.UninstallExtension(uuid).done(function() {
                dbusProxy.InstallExtension(uuid);
            });
        }

        $switch.bind('changed', function(e, newValue) {
            var oldState = $elem.data('state');
            if (newValue) {
                if (oldState == ExtensionState.UNINSTALLED) {
                    // If the extension is uninstalled and we
                    // flick the switch on, install.
                    dbusProxy.InstallExtension(uuid);
                    sendPopularity('enable');
                } else if (oldState == ExtensionState.DISABLED ||
                           oldState == ExtensionState.INITIALIZED) {
                    dbusProxy.EnableExtension(uuid);
                    sendPopularity('enable');
                }
            } else {
                if (oldState == ExtensionState.ENABLED) {
                    dbusProxy.DisableExtension(uuid);
                    sendPopularity('disable');
                }
            }
        });

        $elem.bind('state-changed', function(e, newState) {
            $elem.data('state', newState);

            $elem.toggleClass('configurable', meta.hasPrefs && newState !== ExtensionState.OUT_OF_DATE);

            if (newState == ExtensionState.DISABLED ||
                newState == ExtensionState.INITIALIZED ||
                newState == ExtensionState.UNINSTALLED) {
                $switch.switchify('activate', false);
            } else if (newState == ExtensionState.ENABLED) {
                $switch.switchify('activate', true);
                $elem.removeClass('out-of-date');
            } else if (newState == ExtensionState.ERROR) {
                $switch.switchify('customize', "ERROR", 'error');
            } else if (newState == ExtensionState.OUT_OF_DATE) {
                var svm = meta.shell_version_map || $elem.data('svm');
                var version = extensionUtils.grabProperExtensionVersion(svm, dbusProxy.ShellVersion);
                $elem.addClass('out-of-date');
                if (version === null) {
                    $switch.switchify('customize', "OUTDATED", 'outdated');
                } else {
                    $switch.switchify('customize', "UPDATE", 'update').on('click', upgradeExtension);
                }
            }

            if ($elem.data('uninstalled') && (newState == ExtensionState.ENABLED ||
                                              newState == ExtensionState.ERROR ||
                                              newState == ExtensionState.OUT_OF_DATE)) {
                $elem.fadeIn({ queue: false }).slideDown();
                $elem.data('uninstalled', false);
                $elem.data('undo-uninstall-message').slideUp();
            }

        });
        $elem.trigger('state-changed', _state);
        elems[uuid] = $elem;
    }

    $.fn.addLocalExtensions = function () {
        return this.each(function() {
            var $container = $(this);
            dbusProxy.ListExtensions().done(function(extensions) {
                if (extensions && !$.isEmptyObject(extensions)) {
                    var extensionValues = [];
                    for (var uuid in extensions) {
                        extensionValues.push(extensions[uuid]);
                    }

                    extensionValues.sort(function(a, b) {
                        if (a.name === undefined)
                            return 0;

                        if (b.name === undefined)
                            return 0;

                        return a.name.localeCompare(b.name);
                    });

                    extensionValues.forEach(function(extension) {
                        var uuid = extension.uuid;

                        function reinstall() {
                            dbusProxy.InstallExtension(uuid);

                            // If the user clicks "Install" we need to show that we
                            // installed it by reattaching the element, but we can't do
                            // that here -- the user might click "Cancel".
                            $elem.data('uninstalled', true);
                        }

                        function uninstall() {
                            var svm = extension.shell_version_map;
                            var wantUndo = (extensionUtils.grabProperExtensionVersion(svm, dbusProxy.ShellVersion) !== null);

                            dbusProxy.UninstallExtension(uuid).done(function(result) {
                                if (result) {
                                    $elem.fadeOut({ queue: false }).slideUp({ queue: false });

                                    if (wantUndo) {
                                        var $message = messages.addInfo(templates.extensions.uninstall(extension));
                                        $message.delegate('a', 'click', reinstall);
                                        $elem.data('undo-uninstall-message', $message);
                                    }
                                }
                            });
                        }

                        // Give us a dummy element that we'll replace when
                        // rendering below, to keep renderExtension simple.
                        var $elem = $('<a>');

                        function renderExtension() {
                            extension.want_uninstall = true;
                            if (extension.description)
                                extension.first_line_of_description = extension.description.split('\n')[0];

                            $elem = $(templates.extensions.info(extension)).replaceAll($elem);
                            $elem.find('.uninstall').on('click', uninstall);

                            addExtensionSwitch(uuid, $elem, extension);
                        }

                        $.ajax({
                            url: "/ajax/detail/",
                            dataType: "json",
                            data: { uuid: extension.uuid,
                                    version: extension.version },
                            type: "GET",
                        }).done(function(result) {
                            $.extend(extension, result);
                            renderExtension();
                        }).fail(function(error) {
                            // Had an error looking up the data for the
                            //extension -- that's OK, just render it anyway.
                            renderExtension();
                        });

                        $container.append($elem);
                    });
                } else {
                    $container.append("You don't have any extensions installed.");
                }
            })
        });
    };

    $.fn.fillInErrors = function () {
        return this.each(function() {
            var $form = $(this);
            var uuid = $form.data('uuid');
            var $textarea = $form.find('textarea');
            dbusProxy.GetExtensionInfo(uuid).done(function(meta) {
                dbusProxy.GetErrors($form.data('uuid')).done(function(errors) {
                    var context = { sv: dbusProxy.ShellVersion,
                                    ev: (meta && meta.version) ? meta.version : null,
                                    errors: errors };

                    $textarea.text(templates.extensions.error_report_template(context));
                });
            });
        });
    };

    $.fn.addExtensionSwitch = function () {
        return this.each(function() {
            var $extension = $(this);
            var uuid = $extension.data('uuid');

            $extension.bind('out-of-date', function() {
                var svm = $extension.data('svm');
                var nhvOperation = extensionUtils.findNextHighestVersion(svm, dbusProxy.ShellVersion);
                if (nhvOperation.operation === 'upgrade' &&
                    nhvOperation.stability === 'stable') {
                    messages.addError("This extension is incompatible with your version of GNOME. Please upgrade to GNOME " + nhvOperation.version);
                } else if (nhvOperation.operation === 'upgrade' &&
                           nhvOperation.stability === 'unstable') {
                    messages.addError("This extension is incompatible with your version of GNOME. This extension supports the GNOME unstable release, " + nhvOperation.version);
                } else if (nhvOperation.operation === 'downgrade') {
                    messages.addError("This extension is incompatible with your version of GNOME.");
                }
            });

            dbusProxy.GetExtensionInfo(uuid).done(function(meta) {
                addExtensionSwitch(uuid, $extension, meta);
            });
        });
    };

    $.fn.grayOutIfOutOfDate = function() {
        return this.each(function() {
            var $elem = $(this);
            var svm = $elem.data('svm');
            if (!svm)
                return;

            var vpk = extensionUtils.grabProperExtensionVersion(svm, dbusProxy.ShellVersion);
            if (vpk === null)
                $elem.addClass('out-of-date');
        });
    };
});
