
from django.contrib.auth import models
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from review.models import CodeReview
from extensions.models import Extension

from decorators import ajax_view, post_only_view
from utils import render

def profile(request, user):
    userobj = get_object_or_404(models.User, username=user)

    template = 'registration/profile.html'
    if request.user == userobj:
        template = 'registration/profile_edit.html'

    display_name = userobj.get_full_name() or userobj.username
    extensions = Extension.objects.filter(creator=userobj)
    reviews = CodeReview.objects.filter(reviewer=userobj)

    return render(request, template, dict(user=userobj,
                                          display_name=display_name,
                                          extensions=extensions,
                                          reviews=reviews,))

@ajax_view
@post_only_view
@login_required
def ajax_change_display_name(request):
    if request.POST['id'] != 'new_display_name':
        return HttpResponseForbidden()

    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    # display name is "%s %s" % (first_name, last_name). Change the first name.
    request.user.first_name = request.POST['value']
    request.user.save()
    return request.POST['value']

@login_required
def profile_redirect(request):
    return redirect('auth-profile', user=request.user.username)
