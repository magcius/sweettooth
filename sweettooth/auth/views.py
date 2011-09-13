
from django.contrib.auth import forms, models
from django.contrib.auth.views import login, logout
from django.shortcuts import get_object_or_404, render

from review.models import CodeReview
from extensions.models import Extension

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
    userobj = get_object_or_404(models.User, username=user)

    template = 'auth/profile.html'
    if request.user == user:
        template = 'auth/profile-edit.html'

    display_name = userobj.get_full_name() or userobj.username
    extensions = Extension.objects.filter(creator=userobj)
    reviews = CodeReview.objects.filter(reviewer=userobj)

    return render(request, template, dict(user=userobj,
                                          display_name=display_name,
                                          extensions=extensions,
                                          reviews=reviews,))

def register(request):
    return None
