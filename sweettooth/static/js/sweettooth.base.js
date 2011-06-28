(function($) {
    var SweetTooth = window.SweetTooth = {};

    SweetTooth.ExtensionState = {
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

    SweetTooth.DBusProxyInterfaces = {
        Available: []
    };

    // layout
    $(document).ready(function() {
        $("#login_link").click(function(event) {
            $(this).toggleClass("selected");
            $("#login_popup_form").slideToggle();
            event.preventDefault();
            return false;
        });
    });
})(jQuery);
