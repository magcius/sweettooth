
from django.contrib.auth.models import User, Permission, Group
from django.db import models
from django.db.models import Q

from extensions import models as extensions_models

def get_all_reviewers():
    perm = Permission.objects.get(codename="can-review-extensions")

    # Dark magic to get all the users with a specific permission
    # Thanks to <schinckel> in #django
    groups = Group.objects.filter(permissions=perm)
    return User.objects.filter(Q(is_superuser=True)|Q(user_permissions=perm)|Q(groups__in=groups)).distinct()

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
