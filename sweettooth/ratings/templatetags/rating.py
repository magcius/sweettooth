
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

class ReadonlyRatingNode(template.Node):
    def __init__(self, value, out_of):
        self.value = template.Variable(value)
        self.out_of = template.Variable(out_of)

    def render(self, context):
        value = self.value.resolve(context)
        out_of = self.out_of.resolve(context)
        parts = []

        for i in xrange(out_of):
            attrs = u' disabled="disabled"'
            if value == i:
                attrs += u' checked="checked"'
            parts.append(u'<input type="radio"%s>' % (attrs,))

        return mark_safe(u'\n'.join(parts))

@register.tag
def rating(parser, token):
    try:
        tag_name, value, out_of = token.split_contents()

    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]

    return ReadonlyRatingNode(value, out_of)
