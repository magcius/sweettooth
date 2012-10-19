
from django.contrib.auth import models
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from review.models import CodeReview
from extensions.models import Extension, ExtensionVersion

from decorators import ajax_view
from utils import render

def profile(request, user):
    userobj = get_object_or_404(models.User, username=user)

    is_editable = request.user == userobj

    display_name = userobj.get_full_name() or userobj.username
    extensions = Extension.objects.visible().filter(creator=userobj).order_by('name')

    if is_editable:
        unreviewed = ExtensionVersion.objects.unreviewed().filter(creator=userobj)
    else:
        unreviewed = []

    return render(request,
                  'registration/profile.html',
                  dict(user=userobj,
                       display_name=display_name,
                       extensions=extensions,
                       unreviewed=nureviewed,
                       is_editable=is_editable))

@ajax_view
@require_POST
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
