"use strict";

define(['jquery'], function($) {

    // jQuery doesn't support events in the capturing phase natively.
    // This is a trick that fires jQuery's event handler during the
    // capturing phase.
    function captureHandler() {
        $.event.handle.apply(document.body, arguments);
    }

    function activateModal(elem, closeFunction) {
        $(document.body).click(function(e) {
            // If the user clicked inside the modal popup, don't
            // close it.
            if ($(elem).has(e.target).length) {
                return true;
            }

            if (closeFunction()) {
                $(document.body).unbind(e);
                document.body.removeEventListener('click', captureHandler, true);
                return false;
            }

            return true;
        });

        document.body.addEventListener('click', captureHandler, true);
    }

    return {
        activateModal: activateModal
    };

});
