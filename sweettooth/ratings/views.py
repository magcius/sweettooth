
import json

from django.core.urlresolvers import reverse
from django.contrib import comments
from django.contrib.messages import info
from django.shortcuts import redirect
from django.utils.dateformat import format as format_date

from extensions import models
from decorators import ajax_view, model_view
from utils import gravatar_url

def comment_done(request):
    pk = request.GET['c']
    comment = comments.get_model().objects.get(pk=pk)
    info(request, "Thank you for your comment")
    return redirect(comment.get_content_object_url())

def comment_details(request, comment):
    extension = comment.content_object
    gravatar = gravatar_url(request, comment.email)
    is_extension_creator = (comment.user == extension.creator)

    return dict(gravatar = gravatar,
                is_extension_creator = is_extension_creator,
                rating = comment.rating,
                comment = comment.comment,
                author = dict(username=comment.user.username,
                              url=reverse('auth-profile', kwargs=dict(user=comment.user.username))),
                date = dict(timestamp = comment.submit_date.isoformat(),
                            standard = format_date(comment.submit_date, 'F j, Y')))

@ajax_view
def get_comments(request):
    extension = models.Extension.objects.get(pk=request.GET['pk'])
    show_all = json.loads(request.GET.get('all', 'false'))

    comment_list = comments.get_model().objects.for_model(extension)
    if not show_all:
        comment_list = comment_list[:5]

    return [comment_details(request, comment) for comment in comment_list]
