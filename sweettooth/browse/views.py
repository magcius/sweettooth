
import json

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from extensions.models import Extension

def detail(request, slug, ver):
    extension = get_object_or_404(Extension, is_published=True, slug=slug)
    version = extension.get_version(ver)
    return render(request, 'detail.html', dict(version=version, extension=extension))

def manifest(request, slug):
    extension = get_object_or_404(Extension, is_published=True, slug=slug)
    version = extension.get_version(request.get('version'))

    return HttpResponse(version.extra_json_data,
                        content_type='application/x-shell-extension')

def download(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.get('version'))

    url = reverse('ext-url', kwargs=dict(filepath=version.source.url))
    return redirect(request.build_absolute_url(url))
