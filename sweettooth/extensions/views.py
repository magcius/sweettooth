
import json

from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from extensions.models import ExtensionVersion

def manifest(request, uuid, ver):
    version = get_object_or_404(ExtensionVersion, pk=ver)

    url = reverse('extensions-download', kwargs=dict(uuid=uuid, ver=ver))

    manifestdata = version.make_metadata_json()
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata),
                        content_type="application/json")

def download(request, uuid, ver):
    version = get_object_or_404(ExtensionVersion, pk=ver)
    return redirect(version.source.url)
