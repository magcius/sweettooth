
from django.contrib import auth
from django.db import models
from django.dispatch import Signal
from extensions.models import ExtensionVersion

class ErrorReport(models.Model):
    comment = models.TextField(blank=True)
    user = models.ForeignKey(auth.models.User, related_name="+")
    version = models.ForeignKey(ExtensionVersion)
    can_contact = models.BooleanField()

error_reported = Signal(providing_args=["request", "version", "report"])
