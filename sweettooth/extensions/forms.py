
from django import forms

class UploadForm(forms.Form):
    source = forms.FileField()
