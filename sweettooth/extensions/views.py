
import json

from tagging.models import Tag

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import DetailView

from extensions import models
from extensions.forms import UploadScreenshotForm, UploadForm, ExtensionDataForm

def manifest(request, uuid, ver):
    version = get_object_or_404(models.ExtensionVersion, pk=ver)

    url = reverse('extensions-download', kwargs=dict(uuid=uuid, ver=ver))

    manifestdata = version.make_metadata_json()
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata),
                        content_type="application/json")

def download(request, uuid, ver):
    version = get_object_or_404(models.ExtensionVersion, pk=ver)
    return redirect(version.source.url)

class ExtensionLatestVersionView(DetailView):
    model = models.Extension
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
        return extension.latest_version

class ExtensionVersionView(DetailView):
    model = models.ExtensionVersion
    context_object_name = "version"
    template_name = "extensions/detail.html"

@login_required
def upload_screenshot(request, pk):
    extension = get_object_or_404(models.Extension, pk=pk)
    if not extension.user_has_access(request.user):
        return

    if request.method == 'POST':
        form = UploadScreenshotForm(request.POST, request.FILES)
        if form.is_valid():
            screenshot = form.save(commit=False)
            screenshot.extension = extension
            screenshot.save()

        return redirect('extensions-detail', pk=extension.pk)
    else:
        form = UploadScreenshotForm(initial=dict(extension=extension))

    return render(request, 'extensions/upload-screenshot.html', dict(form=form))

@login_required
def upload_file(request, pk):
    if pk is None:
        extension = None
    else:
        extension = models.Extension.objects.get(pk=pk)
        if extension.creator != request.user:
            return HttpResponseForbidden()

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_source = form.cleaned_data['source']
            extension, version = models.ExtensionVersion.from_zipfile(file_source, extension)
            extension.creator = request.user
            extension.save()

            version.extension = extension
            version.source = file_source
            version.status = models.STATUS_NEW
            version.save()

            return redirect('extensions-edit-data', pk=version.pk)
    else:
        form = UploadForm()

    return render(request, 'extensions/upload-file.html', dict(form=form))

@login_required
def upload_edit_data(request, pk):
    try:
        version = models.ExtensionVersion.objects.get(pk=pk)
    except models.ExtensionVersion.DoesNotExist:
        return HttpResponseForbidden()

    extension = version.extension
    if version.status in models.REVIEWED_STATUSES:
        return HttpResponseForbidden()

    if not extension.user_has_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ExtensionDataForm(request.POST)
        if form.is_valid():
            extension.name = form.cleaned_data['name']
            extension.description = form.cleaned_data['description']
            extension.url = form.cleaned_data['url']
            extension.save()

            version.replace_metadata_json()
            # XXX: for now until code review happens
            version.status = models.STATUS_ACTIVE
            version.save()

            return redirect('extensions-detail', pk=extension.pk)
    else:
        initial = dict(name=extension.name,
                       description=extension.description,
                       url=extension.url)

        form = ExtensionDataForm(initial=initial)

    return render(request, 'extensions/upload-edit-data.html', dict(form=form))
