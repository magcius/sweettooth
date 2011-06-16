
import json

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from extensions.models import Extension

def detail(request, slug, ver):
    extension = get_object_or_404(Extension, is_published=True, slug=slug)
    version = extension.get_version(ver)

    manifest_url = reverse('ext-manifest', kwargs=dict(uuid=extension.uuid))
    manifest_url = request.build_absolute_uri(manifest_url)

    if ver not in (None, 'latest'):
        manifest_url += '?version=%d' % (ver,)

    template_args = dict(version=version, extension=extension, manifest=manifest_url)
    return render(request, 'detail.html', template_args)

def manifest(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    return HttpResponse(version.extra_json_fields,
                        content_type='application/x-shell-extension')

def download(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    url = reverse('ext-url', kwargs=dict(filepath=version.source.url))
    return redirect(request.build_absolute_uri(url))

def command(request, uuid, cmd):
    data = {'arg': uuid,
            'command': cmd}

    return HttpResponse(json.dumps(data),
                        content_type='application/x-shell-command')
