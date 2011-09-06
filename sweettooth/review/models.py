
from django.contrib.auth.models import User
from django.db import models

from extensions import models as extensions_models

class CodeReview(models.Model):
    reviewer = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()
    version = models.ForeignKey(extensions_models.ExtensionVersion, related_name="reviews")
    newstatus = models.PositiveIntegerField(choices=extensions_models.STATUSES.items())

    @property
    def is_rejected(self):
        return self.newstatus == extensions_models.STATUS_REJECTED

    @property
    def is_active(self):
        return self.newstatus == extensions_models.STATUS_ACTIVE

    class Meta:
        permissions = (
            ("can-review-extensions", "Can review extensions"),
        )
