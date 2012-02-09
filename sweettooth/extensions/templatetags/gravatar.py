from django import template
import urllib, hashlib

register = template.Library()

GRAVATAR_BASE = "https://secure.gravatar.com/avatar/%s?%s"

@register.simple_tag
def gravatar_url(request, email, size=70):
    email_md5 = hashlib.md5(email.lower()).hexdigest()
    default = request.build_absolute_uri("/static/images/nobody.png")
    options = urllib.urlencode(dict(d=default, s=size))

    return GRAVATAR_BASE % (email_md5, options)
