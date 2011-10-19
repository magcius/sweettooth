
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.safestring import mark_safe

import functools
import json

def model_view(model):
    def inner(view):
        @functools.wraps(view)
        def new_view(request, pk, **kw):
            obj = get_object_or_404(model, pk=pk)
            return view(request, obj, **kw)
        return new_view
    return inner

def post_only_view(view):
    @functools.wraps(view)
    def new_view(request, **kw):
        if request.method != 'POST':
            return HttpResponseForbidden()
        return view(request, **kw)
    return new_view

def ajax_view(view):
    @functools.wraps(view)
    def new_view(request, **kw):
        response = view(request, **kw)
        if response is None:
            return HttpResponse()
        if not isinstance(response, HttpResponse):
            response = HttpResponse(mark_safe(json.dumps(response)),
                                    content_type="application/json")
        return response

    return new_view
