
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def paginator(page_obj, context=3):
    number = page_obj.number
    context_left = range(max(number-context, 2), number)
    context_right = range(number+1, min(number+context+1, page_obj.paginator.num_pages+1))

    lines = []

    if page_obj.has_previous():
        lines.append(u'<a class="number prev" href="?page=%d">Previous</a>' % (number-1,))
        lines.append(u'<a class="number first" href="?page=1">1</a>')
        if number-context > 2:
            lines.append(u'<span class="ellipses">...</span>')

        for i in context_left:
            lines.append(u'<a class="prev number" href="?page=%d">%d</a>' % (i, i))

    lines.append(u'<span class="current number">%d</span>' % (number,))

    if page_obj.has_next():
        for i in context_right:
            lines.append(u'<a class="next number" href="?page=%d">%d</a>' % (i, i))
        lines.append(u'<a class="number prev" href="?page=%d">Next</a>' % (number+1,))

    return mark_safe(u'\n'.join(lines))
