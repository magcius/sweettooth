
from django.contrib.auth import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.shortcuts import get_object_or_404, render, redirect

from review.models import CodeReview
from extensions.models import Extension

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

@login_required
def profile_redirect(request):
    return redirect('auth-profile', user=request.user.username)

def register(request):
    return None
