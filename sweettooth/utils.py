
from django.shortcuts import render_to_response
from django.template import RequestContext

def render(req, *args, **kwargs):
    return render_to_response(context_instance=RequestContext(req), *args, **kwargs)
