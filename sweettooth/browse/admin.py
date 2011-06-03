
from django.contrib import admin
from browse.models import Extension

class ExtensionAdmin(admin.ModelAdmin):
    list_display = 'name', 'uploader'

admin.site.register(Extension, ExtensionAdmin)
