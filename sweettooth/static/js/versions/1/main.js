// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery', 'dbus!API', 'versions/common/common'], function($, API, common) {
    "use strict";

    var proxy = {
        IsDummy: false,

        ListExtensions: common.ListExtensions,
        GetExtensionInfo: common.GetExtensionInfo,
        GetErrors: common.GetErrors,
        EnableExtension: common.EnableExtension,
        DisableExtension: common.DisableExtension,
        InstallExtension: common.InstallExtensionTwo,
        UninstallExtension: common.UninstallExtension,
        LaunchExtensionPrefs: common.LaunchExtensionPrefsDummy,

        ShellVersion: API.shellVersion,

        extensionStateChangedHandler: null
    };

    API.onchange = common.API_onchange(proxy);

    return proxy;
});
