
import autoslug
from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Extension(models.Model):
    name = models.CharField(max_length = 200)
    uploader = User()
    slug = autoslug.AutoSlugField(populate_from = "name")
