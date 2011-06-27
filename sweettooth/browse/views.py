
import json

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from extensions.models import Extension

def get_manifest_url(request, extension, ver):
    manifest_url = reverse('ext-manifest', kwargs=dict(uuid=extension.uuid))
    manifest_url = request.build_absolute_uri(manifest_url)

    if ver not in (None, 'latest'):
        manifest_url += '?version=%d' % (ver,)

    return manifest_url

def list_ext(request):
    extensions = Extension.objects.filter(is_published=True)
    extensions_list = ((ext, ext.get_version('latest')) for ext in extensions)
    return render(request, 'list.html', dict(extensions_list=extensions_list))

def detail(request, slug, ver):
    extension = get_object_or_404(Extension, is_published=True, slug=slug)
    version = extension.get_version(ver)

    template_args = dict(version=version,
                         extension=extension,
#                         manifest=get_manifest_url(request, extension, version))
                         )
    return render(request, 'detail.html', template_args)

def manifest(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    url = reverse('ext-download', kwargs=dict(uuid=uuid))
    url += '?version=%d' % (version.version,)

    manifestdata = json.loads(version.extra_json_fields)
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata),
                        content_type='application/x-shell-extension')

def download(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    url = reverse('ext-url', kwargs=dict(filepath=version.source.url))
    return redirect(request.build_absolute_uri(url))
