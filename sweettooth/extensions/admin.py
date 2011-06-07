
from django.contrib import admin
from extensions.models import Extension

class ExtensionAdmin(admin.ModelAdmin):
    list_display = 'name', 'creator'

admin.site.register(Extension, ExtensionAdmin)
