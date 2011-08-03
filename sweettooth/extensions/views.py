
import json

from tagging.models import Tag

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import DetailView

from extensions.models import Extension, ExtensionVersion, Screenshot
from extensions.forms import UploadScreenshotForm, UploadForm, ExtensionDataForm

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

class ExtensionLatestVersionView(DetailView):
    model = Extension
    context_object_name = "version"
    template_name = "extensions/detail.html"

    def get(self, request, **kwargs):
        # Redirect if we don't match the slug.
        slug = self.kwargs.get('slug')
        self.object = self.get_object()
        if slug == self.object.extension.slug:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        kwargs = dict(self.kwargs)
        kwargs.update(dict(slug=self.object.extension.slug))
        return redirect('extensions-detail', **kwargs)

    def get_object(self):
        extension = super(ExtensionLatestVersionView, self).get_object()
        return extension.get_latest_version()

class ExtensionVersionView(DetailView):
    model = ExtensionVersion
    context_object_name = "version"
    template_name = "extensions/detail.html"

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

        return redirect('extensions-detail', pk=extension.pk)
    else:
        form = UploadScreenshotForm(initial=dict(extension="FOO"))

    return render(request, 'extensions/upload-screenshot.html', dict(form=form))

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


@login_required
def upload_file(request, pk):
    if pk is None:
        extension = None
    else:
        extension = Extension.objects.get(pk=pk)
        if extension.creator != request.user:
            return HttpResponseForbidden()

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_source = form.cleaned_data['source']
            extension, version = ExtensionVersion.from_zipfile(file_source, extension)
            extension.creator = request.user
            extension.save()

            version.extension = extension
            version.source = file_source
            version.is_published = False
            version.save()

            return redirect('extensions-edit-data', pk=version.pk)
    else:
        form = UploadForm()

    return render(request, 'extensions/upload-file.html', dict(form=form))

@login_required
def upload_edit_data(request, pk):
    try:
        version = ExtensionVersion.objects.get(pk=pk)
    except ExtensionVersion.DoesNotExist:
        return HttpResponseForbidden()

    extension = version.extension
    if extension.is_published:
        return HttpResponseForbidden()

    if (extension.creator != request.user and not \
        request.user.has_perm('extensions.can-modify-data')):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ExtensionDataForm(request.POST)
        if form.is_valid():
            extension.name = form.cleaned_data['name']
            extension.description = form.cleaned_data['description']
            extension.url = form.cleaned_data['url']
            extension.is_published = True
            extension.save()

            version.replace_metadata_json()
            version.save()

            return redirect('extensions-detail', pk=extension.pk)
    else:
        initial = dict(name=extension.name,
                       description=extension.description,
                       url=extension.url)

        form = ExtensionDataForm(initial=initial)

    return render(request, 'extensions/upload-edit-data.html', dict(form=form))
