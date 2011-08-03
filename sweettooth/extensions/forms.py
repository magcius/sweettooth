
from django import forms
from extensions import models

class UploadScreenshotForm(forms.ModelForm):
    class Meta:
        model = models.Screenshot
        exclude = 'extension',

class UploadForm(forms.Form):
    source = forms.FileField()

class ExtensionDataForm(forms.Form):
    name = forms.CharField(label="Name", max_length = 200)
    description = forms.CharField(label="Description", widget = forms.Textarea)
    url = forms.URLField(label="Author URL")
