
from django.contrib.auth import models
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.shortcuts import get_object_or_404, render, redirect

from auth import forms

from review.models import CodeReview
from extensions.models import Extension

def profile(request, user):
    userobj = get_object_or_404(models.User, username=user)

    template = 'auth/profile.html'
    if request.user == user:
        template = 'auth/profile_edit.html'

    display_name = userobj.get_full_name() or userobj.username
    extensions = Extension.objects.filter(creator=userobj)
    reviews = CodeReview.objects.filter(reviewer=userobj)

    return render(request, template, dict(user=userobj,
                                          display_name=display_name,
                                          extensions=extensions,
                                          reviews=reviews,))

@login_required
def profile_redirect(request):
    return redirect('auth-profile', user=request.user.username)

def register(request):
    if request.method == 'POST':
        form = forms.UserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # We want to log the user in after this.
            # The user object that was just returned isn't "authenticated",
            # so a login will fail. The user model doesn't have the real
            # password, but a hash of it, so grab the data from the form.
            authed_user = authenticate(username=form.cleaned_data['username'],
                                       password=form.cleaned_data['password1'])
            auth_login(request, authed_user)

            # Then bounce him to his profile afterwards.
            return redirect('auth-profile', user=user.username)
    else:
        form = forms.UserCreationForm()

    return render(request, 'auth/register.html', dict(form=form))
