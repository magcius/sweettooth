"use strict";

define(['jquery', 'dbus!API', 'versions/common/common'], function($, API, common) {
    var proxy = {
        ListExtensions: common.ListExtensions,
        GetExtensionInfo: common.GetExtensionInfo,
        GetErrors: common.GetErrors,
        EnableExtension: common.EnableExtension,
        DisableExtension: common.DisableExtension,
        InstallExtension: common.InstallExtension,
        UninstallExtension: common.UninstallExtension,

        ShellVersion: API.shellVersion,

        extensionStateChangedHandler: null,
        shellRestartHandler: null
    };

    API.onchange = common.API_onchange(proxy);
    API.onshellrestart = common.API_onshellrestart(proxy);

    return proxy;
});
