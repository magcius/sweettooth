"use strict";

define(['jquery'], function($) {
    function addMessage(tag, message) {
        $('#message_container').append(
            $('<p>')
                .addClass('message')
                .addClass(tag)
                .text(message));
    }

    function addError(message) {
        return addMessage('error', message);
    }

    return {
        addMessage: addMessage,
        addError: addError
    };
});
