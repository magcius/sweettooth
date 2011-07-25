
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from extensions.models import Extension, ExtensionVersion

EXTENSION_DATA_KEY = "extension data"

class UploadForm(forms.Form):
    source = forms.FileField()

class ExtensionDataForm(forms.Form):
    name = forms.CharField(label="Name", max_length = 200)
    description = forms.CharField(label="Description", widget = forms.Textarea)
    url = forms.URLField(label="Author URL")

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

            request.session[EXTENSION_DATA_KEY] = extension, version
            return redirect(reverse('upload-edit-data'))
    else:
        form = UploadForm()

    return render(request, 'upload-file.html', dict(form=form))

@login_required
def upload_edit_data(request):
    extension, version = request.session.get(EXTENSION_DATA_KEY, (None, None))
    if extension is None or version is None:
        return redirect(reverse('upload-file'))

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

            del request.session[EXTENSION_DATA_KEY]
            return redirect(reverse('ext-detail', kwargs=dict(pk=extension.pk)))
    else:
        initial = dict(name=extension.name,
                       description=extension.description,
                       url=extension.url)

        form = ExtensionDataForm(initial=initial)

    return render(request, 'upload-edit-data.html', dict(form=form))
