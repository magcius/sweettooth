
import json

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin
from django.utils.safestring import mark_for_escaping

from extensions import models
from extensions.forms import UploadForm, ExtensionDataForm

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
        if self.object is None:
            raise Http404()

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

    def get(self, request, **kwargs):
        self.object = self.get_object()

        if self.object is None:
            raise Http404()

        is_preview = False
        if self.object.status == models.STATUS_NEW:
            # If it's unreviewed and unlocked, this is a preview
            # for pre-lock.
            is_preview = True

            # Don't allow anybody (even moderators) to peek pre-lock.
            if self.object.extension.creator != request.user:
                raise Http404()

        # Redirect if we don't match the slug or extension PK.
        slug = self.kwargs.get('slug')
        extpk = self.kwargs.get('ext_pk')
        try:
            extpk = int(extpk)
        except ValueError:
            extpk = None

        if slug == self.object.extension.slug and extpk == self.object.extension.pk:
            context = self.get_context_data(object=self.object)
            context['is_preview'] = is_preview
            return self.render_to_response(context)

        kwargs = dict(self.kwargs)
        kwargs.update(dict(slug=self.object.extension.slug,
                           ext_pk=self.object.extension.pk))
        return redirect('extensions-version-detail', **kwargs)

class AjaxInlineEditView(SingleObjectMixin, View):
    model = models.Extension

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        key = self.request.POST['id']
        value = self.request.POST['value']
        if key.startswith('extension_'):
            key = key[len('extension_'):]

        whitelist = 'name', 'description', 'url'
        if key not in whitelist:
            return HttpResponseForbidden()

        setattr(self.object, key, value)
        self.object.save()

        return HttpResponse(mark_for_escaping(value))

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

            return redirect('extensions-version-detail',
                            pk=version.pk,
                            ext_pk=extension.pk,
                            slug=extension.slug)
    else:
        form = UploadForm()

    return render(request, 'extensions/upload-file.html', dict(form=form))
