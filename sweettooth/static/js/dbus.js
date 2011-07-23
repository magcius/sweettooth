"use strict";

require(['jquery'], function($) {
    var MIME_TYPE = 'application/x-gnome-shell-integration';
    var $plg = $('<embed>', { type: MIME_TYPE });

    // Netscape plugins are strange: if you make them invisible with
    // CSS or give them 0 width/height, they won't load. Just smack it
    // off-screen so it isn't visible, but still works.
    $plg.css({ position: 'absolute',
               left: '-1000em',
               top: '-1000em' });
    $(document.body).append($plg);

    var plg = $plg[0];

    // Play some magic with require.js to pass the plugin
    // object to our proxy.
    define('_DBUS_PLG', [], function() {
        return plg;
    });
    
    var apiVersion = plg.apiVersion;
    var scriptname = null;
    if (apiVersion)
        scriptname = './versions/' + apiVersion + '/main';

    // We need to abuse the plugin system so that we can defer the
    // load completion until our dynamically built requirement is
    // loaded.
    define({
        load: function(name, req, onLoad, config) {
            if (!scriptname) {
                onLoad();
            }

            req([scriptname], function(module) {
                onLoad(module);
            });
        }
    });
});
