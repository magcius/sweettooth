
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

class GetManifestURLNode(template.Node):
    def __init__(self, version):
        self.version = template.Variable(version)

    def render(self, context):
        version = self.version.resolve(context)
        request = template.Variable('request').resolve(context)

        return mark_safe(version.get_manifest_url(request))

@register.tag
def manifest_url(parser, token):
    try:
        tag_name, version = token.split_contents()

    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]

    return GetManifestURLNode(version)
