from django import template
from utils import gravatar_url

register = template.Library()
register.simple_tag(gravatar_url)
