
try:
    import json
except ImportError:
    import simplejson as json

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin
from django.utils.safestring import mark_for_escaping

from extensions import models
from extensions.forms import UploadForm, ExtensionDataForm

def manifest(request, uuid, ver):
    version = get_object_or_404(models.ExtensionVersion, pk=ver)

    if version.status != models.STATUS_ACTIVE:
        return HttpResponseForbidden()

    url = reverse('extensions-download', kwargs=dict(uuid=uuid, ver=ver))

    manifestdata = version.make_metadata_json()
    manifestdata['__installer'] = request.build_absolute_uri(url)

    return HttpResponse(json.dumps(manifestdata),
                        content_type="application/json")

def download(request, uuid, ver):
    version = get_object_or_404(models.ExtensionVersion, pk=ver)

    if version.status != models.STATUS_ACTIVE:
        return HttpResponseForbidden()

    return redirect(version.source.url)

class ExtensionLatestVersionView(DetailView):
    model = models.Extension
    context_object_name = "version"

    @property
    def template_name(self):
        # If the user can edit the model, let him do so.
        if self.object.extension.user_has_access(self.request.user):
            return "extensions/detail-edit.html"
        return "extensions/detail.html"

    def get(self, request, **kwargs):
        # Redirect if we don't match the slug.
        slug = self.kwargs.get('slug')
        self.object = self.get_object()
        if self.object is None:
            raise Http404()

        if slug == self.object.extension.slug:
            context = self.get_context_data(object=self.object)
            status = self.object.status
            context['is_editable'] = status in models.EDITABLE_STATUSES
            context['is_visible'] = status in models.VISIBLE_STATUSES
            context['status'] = status
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

    @property
    def template_name(self):
        # If the user can edit the model, let him do so.
        if self.object.extension.user_has_access(self.request.user):
            return "extensions/detail-edit.html"
        return "extensions/detail.html"

    def get(self, request, **kwargs):
        self.object = self.get_object()

        if self.object is None:
            raise Http404()

        is_preview = False
        status = self.object.status
        if status == models.STATUS_NEW:
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
            context['is_editable'] = status in models.EDITABLE_STATUSES
            context['is_visible'] = status in models.VISIBLE_STATUSES
            context['status'] = status
            return self.render_to_response(context)

        kwargs = dict(self.kwargs)
        kwargs.update(dict(slug=self.object.extension.slug,
                           ext_pk=self.object.extension.pk))
        return redirect('extensions-version-detail', **kwargs)

class AjaxSubmitAndLockView(SingleObjectMixin, View):
    model = models.ExtensionVersion

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.extension.user_has_access(request.user):
            return HttpResponseForbidden()

        if self.object.status != models.STATUS_NEW:
            return HttpResponseForbidden()

        self.object.status = models.STATUS_LOCKED
        self.object.save()

        models.submitted_for_review.send(sender=self, version=self.object)

        return HttpResponse()

class AjaxInlineEditView(SingleObjectMixin, View):
    model = models.Extension

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.user_has_access(request.user):
            return HttpResponseForbidden()

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

class AjaxScreenshotUploadView(SingleObjectMixin, View):
    model = models.Extension

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.user_has_access(request.user):
            return HttpResponseForbidden()

        self.object.screenshot = request.FILES['file']
        self.object.save()

        return HttpResponse()

@login_required
def upload_file(request, pk):
    if pk is None:
        extension = models.Extension(creator=request.user)
    else:
        extension = models.Extension.objects.get(pk=pk)
        if extension.creator != request.user:
            return HttpResponseForbidden()

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_source = form.cleaned_data['source']
            version = models.ExtensionVersion()
            version.extension = extension
            version.parse_zipfile(file_source)

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
