
from django.contrib.auth.models import User, Permission, Group
from django.db import models
from django.db.models import Q

from extensions.models import ExtensionVersion, STATUSES

def get_all_reviewers():
    perm = Permission.objects.get(codename="can-approve-extensions")

    # Dark magic to get all the users with a specific permission
    # Thanks to <schinckel> in #django
    groups = Group.objects.filter(permissions=perm)
    return User.objects.filter(Q(is_superuser=True)|Q(user_permissions=perm)|Q(groups__in=groups)).distinct()

class CodeReview(models.Model):
    reviewer = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    version = models.ForeignKey(ExtensionVersion, related_name="reviews")
    changelog = models.OneToOneField('ChangeStatusLog', null=True)

    class Meta:
        permissions = (
            ("can-approve-extensions", "Can approve extensions"),
        )

class ChangeStatusLog(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    newstatus = models.PositiveIntegerField(choices=STATUSES.items())
    version = models.ForeignKey(ExtensionVersion, related_name="status_log")

    def get_newstatus_class(self):
        return STATUSES[self.newstatus].lower()
