
from django.shortcuts import get_object_or_404, render, redirect

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

def extension_download(request, slug, ver):
    extension, version = get_extension(slug, ver)
    return redirect('uploaded-files', version.source.name)
