
from django.contrib.auth import forms as forms

class AutoFocusAuthenticationForm(forms.AuthenticationForm):
    def __init__(self, *a, **kw):
        super(AutoFocusAuthenticationForm, self).__init__(*a, **kw)
        self.fields['username'].widget.attrs['autofocus'] = True

class InlineAuthenticationForm(forms.AuthenticationForm):
    def __init__(self, *a, **kw):
        super(InlineAuthenticationForm, self).__init__(*a, **kw)
        for field in self.fields.itervalues():
            field.widget.attrs['placeholder'] = field.label

def register(request):
    return None
