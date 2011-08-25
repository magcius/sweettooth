
from django.contrib.auth.models import User
from django.db import models

from extensions import models as extensions_models

class CodeReview(models.Model):
    reviewer = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()
    version = models.ForeignKey(extensions_models.ExtensionVersion, related_name="reviews")
    newstatus = models.PositiveIntegerField(choices=extensions_models.STATUSES.items())

    class Meta:
        permissions = (
            ("can-review-extensions", "Can review extensions"),
        )
