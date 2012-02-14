"use strict";

define(['jquery', 'dbus!API', 'versions/common/common'], function($, API, common) {
    var proxy = {
        IsDummy: false,

        ListExtensions: common.ListExtensions,
        GetExtensionInfo: common.GetExtensionInfo,
        GetErrors: common.GetErrors,
        EnableExtension: common.EnableExtension,
        DisableExtension: common.DisableExtension,
        InstallExtension: common.InstallExtension,
        UninstallExtension: common.UninstallExtension,
        LaunchExtensionPrefs: common.LaunchExtensionPrefsDummy,

        ShellVersion: API.shellVersion,

        extensionStateChangedHandler: null
    };

    API.onchange = common.API_onchange(proxy);

    return proxy;
});
