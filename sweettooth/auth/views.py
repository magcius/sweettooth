
from django.contrib.auth import forms, models
from django.contrib.auth.views import login, logout
from django.shortcuts import get_object_or_404, render

class AutoFocusAuthenticationForm(forms.AuthenticationForm):
    def __init__(self, *a, **kw):
        super(AutoFocusAuthenticationForm, self).__init__(*a, **kw)
        self.fields['username'].widget.attrs['autofocus'] = True

class InlineAuthenticationForm(forms.AuthenticationForm):
    def __init__(self, *a, **kw):
        super(InlineAuthenticationForm, self).__init__(*a, **kw)
        for field in self.fields.itervalues():
            field.widget.attrs['placeholder'] = field.label

def profile(request, user):
    user = get_object_or_404(models.User, username=user)

    template = 'auth/profile.html'
    if request.user == user:
        template = 'auth/profile-edit.html'

    display_name = user.get_full_name() or request.user.username
    return render(request, template, dict(user=user, display_name=display_name))

def register(request):
    return None
