
from django.contrib import auth
from django.db import models
from django.dispatch import Signal
from extensions.models import ExtensionVersion

class ErrorReport(models.Model):
    comment = models.TextField(blank=True)

    # In the case that a user isn't logged in, they can supply an optional
    # email address for the extension author to reply to.
    email = models.EmailField(blank=True)

    user = models.ForeignKey(auth.models.User, blank=True, related_name="+")

    version = models.ForeignKey(ExtensionVersion)

    @property
    def user_email(self):
        if self.user:
            return self.user.email
        else:
            return self.email

    @property
    def user_display(self):
        if self.user:
            return self.user.username
        else:
            return self.email
error_reported = Signal(providing_args=["version", "report"])
