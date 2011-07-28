
import json

from tagging.models import TaggedItem
from tagging.utils import get_tag

from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import DetailView
from django import forms

from extensions.models import Extension, ExtensionVersion, Screenshot

class ExtensionLatestVersionView(DetailView):
    model = Extension
    context_object_name = "version"
    template_name = "browse/detail.html"

    def get(self, request, **kwargs):
        # Redirect if we don't match the slug.
        slug = self.kwargs.get('slug')
        self.object = self.get_object()
        if slug == self.object.extension.slug:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        kwargs = dict(self.kwargs)
        kwargs.update(dict(slug=self.object.extension.slug))
        return redirect('browse:detail', **kwargs)

    def get_object(self):
        extension = super(ExtensionLatestVersionView, self).get_object()
        return extension.get_latest_version()

class ExtensionVersionView(DetailView):
    model = ExtensionVersion
    context_object_name = "version"
    template_name = "browse/detail.html"

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

        return redirect('extension:detail', kwargs=dict(pk=extension.pk))
    else:
        form = UploadScreenshotForm(initial=dict(extension="FOO"))

    return render(request, 'browse/upload-screenshot.html', dict(form=form))

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
