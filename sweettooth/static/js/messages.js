// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

define(['jquery'], function($) {
    "use strict";

    var exports = {};

    var $container = $('#message_container');

    var SORT_ORDER = ['error', 'warning', 'info'];

    function grabMessageSort($message) {
        var classList = $message.attr('class').split(' ');

        for (var i = 0; i < classList.length; i ++) {
            var order = SORT_ORDER.indexOf(classList[i]);
            if (order > -1)
                return order;
        }

        return null;
    }

    function compareMessage(a, b) {
        var aSort = grabMessageSort($(a));
        var bSort = grabMessageSort($(b));

        if (aSort !== null && bSort !== null)
            return aSort - bSort;
        return 0;
    }

    function sortMessages() {
        var messages = $container.find('.message');
        messages.sort(compareMessage);

        $container.empty();
        $container.append(messages);
    }

    var addMessage = exports.addMessage = function(tag, message) {
        var message = $('<p>').addClass('message').addClass(tag)
            .append(message).appendTo($container);

        sortMessages();

        return message;
    }

    exports.addInfo = function(message) {
        return addMessage('info', message);
    }

    exports.addWarning = function(message) {
        return addMessage('info', message);
    }

    exports.addError = function(message) {
        return addMessage('error', message);
    }

    return exports;
});
