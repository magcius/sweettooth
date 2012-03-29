"use strict";

define(['jquery', 'dbus!API', 'versions/common/common'], function($, API, common) {
    var proxy = {
        IsDummy: false,

        ListExtensions: common.ListExtensions,
        GetExtensionInfo: common.GetExtensionInfo,
        GetErrors: common.GetErrors,
        EnableExtension: common.EnableExtension,
        DisableExtension: common.DisableExtension,
        InstallExtension: common.InstallExtensionOne,
        UninstallExtension: common.UninstallExtension,
        LaunchExtensionPrefs: common.LaunchExtensionPrefs,

        ShellVersion: API.shellVersion,

        extensionStateChangedHandler: null,
        shellRestartHandler: null
    };

    API.onchange = common.API_onchange(proxy);
    API.onshellrestart = common.API_onshellrestart(proxy);

    return proxy;
});
