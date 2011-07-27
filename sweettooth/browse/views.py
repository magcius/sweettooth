
import json

from tagging.models import TaggedItem
from tagging.utils import get_tag

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, permission_required
from django import forms

from extensions.models import Extension, Screenshot

def get_manifest_url(request, ver):
    manifest_url = reverse('ext-manifest', kwargs=dict(uuid=ver.extension.uuid))
    manifest_url = request.build_absolute_uri(manifest_url)

    if ver not in (None, 'latest'):
        manifest_url += '?version=%d' % (ver.version,)

    return manifest_url

def list_ext(request):
    extensions = Extension.objects.filter(is_published=True)
    extensions_list = ((ext, get_manifest_url(request, ext.get_version('latest'))) for ext in extensions)
    return render(request, 'browse/list.html', dict(extensions_list=extensions_list))

def detail(request, pk, slug):
    extension = get_object_or_404(Extension, is_published=True, pk=pk)
    version_string = request.GET.get('version')
    if slug != extension.slug:
        url = reverse('ext-detail', kwargs=dict(pk=pk, slug=extension.slug))
        if version_string:
            url += '?version=%s' % (version_string,)
        return redirect(url)

    version = extension.get_version(version_string)

    template_args = dict(version=version,
                         extension=extension,
                         manifest=get_manifest_url(request, version))
    return render(request, 'browse/detail.html', template_args)

def manifest(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    url = reverse('ext-download', kwargs=dict(uuid=uuid))
    url += '?version=%d' % (version.version,)

    manifestdata = json.loads(version.extra_json_fields)
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata))

def download(request, uuid):
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)
    version = extension.get_version(request.GET.get('version'))

    url = reverse('ext-url', kwargs=dict(filepath=version.source.url))
    return redirect(request.build_absolute_uri(url))

class UploadScreenshotForm(forms.ModelForm):
    class Meta:
        model = Screenshot
        exclude = 'extension',

@login_required
def upload_screenshot(request, pk):
    extension = get_object_or_404(Extension, pk=pk)
    if request.user.has_perm('extensions.can-modify-data') or extension.creator == request.user:
        pass
    else:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = UploadScreenshotForm(request.POST, request.FILES)
        if form.is_valid():
            screenshot = form.save(commit=False)
            screenshot.extension = extension
            screenshot.save()

        return redirect(reverse('ext-detail', kwargs=dict(pk=extension.pk)))
    else:
        form = UploadScreenshotForm(initial=dict(extension="FOO"))

    return render(request, 'browse/upload-screenshot.html', dict(form=form))

def browse_tag(request, tag):
    tag_inst = get_tag(tag)
    if tag_inst is None:
        extensions_list = []
    else:
        extensions = TaggedItem.objects.get_by_model(Extension, tag_inst)
        extensions_list = ((ext, ext.get_version('latest')) for ext in extensions)
    return render(request, 'browse/list.html', dict(extensions_list=extensions_list))

@permission_required('extensions.can-modify-tags')
def modify_tag(request, tag):
    uuid = request.GET.get('uuid')
    action = request.GET.get('action')
    extension = get_object_or_404(Extension, is_published=True, uuid=uuid)

    if action == 'add':
        Tag.objects.add_tag(extension, tag)
    elif action == 'rm':
        Tag.objects.update_tags(extension, [t for t in extension.tags if t.name != tag])

    return HttpResponse("true" if extension.is_featured() else "false")
