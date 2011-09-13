### gravatar.py ###############
### place inside a 'templatetags' directory inside the top level of a Django app (not project, must be inside an app)
### at the top of your page template include this:
### {% load gravatar %}
### and to use the url do this:
### <img src="{% gravatar_url someone@somewhere.com %}">
### or
### <img src="{% gravatar_url some_template_variable %}">
### just make sure to update the "default" image path below

from django import template
import urllib, hashlib

register = template.Library()

class GravatarUrlNode(template.Node):
    def __init__(self, email, size):
        self.email = template.Variable(email)
        self.size = size

    def render(self, context):
        try:
            email = self.email.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        default = "http://planet.gnome.org/heads/nobody.png"

        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(self.size)})

        return gravatar_url

@register.tag
def gravatar_url(parser, token):
    try:
        # Default of 70 px
        tag_name, email, size = (token.split_contents() + [70])[:3]

    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires one or two arguments" % token.contents.split()[0]

    return GravatarUrlNode(email, size)
