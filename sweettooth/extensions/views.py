
import json

from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from extensions.models import ExtensionVersion

def manifest(request, uuid, ver):
    version = get_object_or_404(ExtensionVersion, pk=ver)

    url = reverse('extension:download', kwargs=dict(uuid=uuid, ver=ver))

    manifestdata = json.loads(version.extra_json_fields)
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata),
                        content_type="application/json")

def download(request, uuid, ver):
    version = get_object_or_404(ExtensionVersion, pk=ver)

    return redirect('extension-data', kwargs=dict(filepath=version.source.url))
