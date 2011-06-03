
import autoslug
from django.contrib import auth
from django.db import models

# Create your models here.

class Extension(models.Model):
    name = models.CharField(max_length = 200)
    uploader = models.ForeignKey(auth.models.User)
    slug = autoslug.AutoSlugField(populate_from = "name")
