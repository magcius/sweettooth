
from django.db import models
from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_will_be_posted

class RatingComment(Comment):
    rating = models.PositiveIntegerField()

def make_sure_user_was_authenticated(sender, comment, request, **kwargs):
    return request.user.is_authenticated()

comment_will_be_posted.connect(make_sure_user_was_authenticated)
