"use strict";

define(['jquery'], function($) {

    function getSides($elem, $slider) {
        var bl = parseInt($elem.css('borderLeftWidth')) + parseInt($slider.css('borderLeftWidth'));
        var br = parseInt($elem.css('borderRightWidth')) + parseInt($slider.css('borderRightWidth'));
        var left = -bl + 1;
        var right = $elem.innerWidth() - $slider.innerWidth() - parseInt($elem.css('borderRightWidth'));
        var center = right / 2 + left;
        return {left: left, right: right, center: center};
    }

    var methods = {
        init: function() {
            return this.each(function() {
                var $elem = $(this);
                var $slider = $('<span>', {'class': 'slider not-dragging'});
                $slider.append($('<span>', {'class': 'handle'}));
                var data = $elem.data('switch');
                if (!data) {
                    data = {};
                    data.activated = undefined;
                    data.insensitive = false;
                    $elem.data('switch', data);
                }

                function mouseup(e) {
                    $slider.addClass('not-dragging');
                    $(document).unbind('mousemove.slider').unbind('mouseup.slider');
                    var s = getSides($elem, $slider);
                    $slider.css('left', data.activated ? s.right : s.left);
                    if (data.activated != data.initialActivated)
                        $elem.trigger('changed', data.activated);
                    return false;
                }

                function mousemove(e) {
                    var s = getSides($elem, $slider);
                    var x = e.pageX - data.initialPageX + data.initialLeft;
                    if (x < s.left)  x = s.left;
                    if (x > s.right) x = s.right;

                    data.activated = x >= s.center;
                    $elem.toggleClass('activated', data.activated);

                    $slider.css('left', x);
                    return false;
                }

                $elem
                    .addClass('_gnome-switch')
                    .append($('<span>', {'class': 'on'}).text("ON"))
                    .append($('<span>', {'class': 'off'}).text("OFF"))
                    .append($slider)

                // Disable selection.
                    .css({'cursor': 'default',
                          '-moz-user-select': 'none'})
                    .attr('unselectable', 'on')
                    .bind('selectstart', function() { return false; });

                methods.activate.call($elem, $elem.hasClass('activated'));
                methods.insensitive.call($elem, $elem.hasClass('insensitive'));

                $slider.bind('mousedown', function(e) {
                    if (data.insensitive)
                        return true;

                    data.initialActivated = data.activated;
                    data.initialPageX = e.pageX;
                    var left = $slider.position().left;
                    data.initialLeft = left;
                    $slider.css({'position': 'absolute', 'left': left});
                    $slider.removeClass('not-dragging');
                    $(document).bind({
                        'mousemove.slider': mousemove,
                        'mouseup.slider': mouseup
                    });
                    return false;
                });

                $elem.bind('click', function(e) {
                    var doToggle;
                    var isActivated = data.activated;
                    if (data.insensitive)
                        return true;

                    if (data.initialPageX === undefined) {
                        doToggle = true;
                    } else {
                        // Make sure we didn't drag before toggling.
                        var travelDistance = Math.abs(e.pageX - data.initialPageX);
                        doToggle = travelDistance < 4 && isActivated == data.initialActivated;

                        delete data.initialActivated;
                        delete data.initialPageX;
                        delete data.initialLeft;
                    }

                    if (doToggle)
                        methods.activate.call($elem, !isActivated);

                    return false;
                });
            });
        },

        activate: function(value) {
            return this.each(function() {
                var $elem = $(this);
                var $slider = $elem.find('span.slider');

                var data = $elem.data('switch');
                if (data.activated == value)
                    return;

                data.activated = value;

                $elem.trigger('changed', value);
                $elem.toggleClass('activated', value);

                var s = getSides($elem, $slider);
                $slider.css('left', value ? s.right : s.left);
                return this;
            });
        },

        insensitive: function(value) {
            return this.each(function() {
                var $elem = $(this);
                var data = $elem.data('switch');
                data.insensitive = value;
                $elem.toggleClass('insensitive', value);
            });
        },
    };

    $.fn.switchify = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.switchify');
        }    
    };

});
