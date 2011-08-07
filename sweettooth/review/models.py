
from django.contrib.auth.models import User
from django.db import models

from extensions.models import ExtensionVersion

class CodeReview(models.Model):
    author = models.ForeignKey(User)
    date = models.DateTimeField()
    overview = models.TextField()
    to = models.ForeignKey(ExtensionVersion)
