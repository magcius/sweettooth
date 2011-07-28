
from django.db import models
from django.contrib.comments.models import Comment

class RatingComment(Comment):
    rating = models.PositiveIntegerField()
