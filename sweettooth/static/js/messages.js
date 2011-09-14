"use strict";

define(['jquery'], function($) {
    function addMessage(tag, message) {
        return $('<p>').addClass('message').addClass(tag)
            .append(message).appendTo($('#message_container'));
    }

    function addInfo(message) {
        return addMessage('info', message);
    }

    function addError(message) {
        return addMessage('error', message);
    }

    return {
        addMessage: addMessage,
        addError: addError,
        addInfo: addInfo
    };
});
