
import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from extensions.models import Extension

def get_extension(slug, ver):
    extension = get_object_or_404(Extension, is_published=True, slug=slug)

    if ver == 'latest':
        version = extension.extensionversion_set.order_by('-version')[0]
    else:
        version = extension.extensionversion_set.get(version=int(ver))

    return extension, version

def extension_detail(request, slug, ver):
    extension, version = get_extension(slug, ver)
    return render(request, 'detail.html', dict(version=version, extension=extension))

def extension_manifest(request, slug):
    ver = request.GET.get('version', 'latest')

    extension, version = get_extension(slug, ver)

    # XXX - this sucks
    url = 'http://extensions.gnome.org/static/extension-data/' + version.source.name
    manifestdata = json.loads(version.extra_json_fields)
    manifestdata.update({'_manifest_url': url})

    return HttpResponse(json.dumps(manifestdata),
                        content_type='application/x-shell-extension')
