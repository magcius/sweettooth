
from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin

from extensions.models import Extension, ExtensionVersion

class ExtensionVersionAdmin(admin.TabularInline):
    model = ExtensionVersion
    fields = 'version', 'status',
    extra = 0

class ExtensionAdmin(admin.ModelAdmin):
    list_display = 'name', 'num_versions', 'creator',
    list_display_links = 'name',

    def num_versions(self, ext):
        return ext.versions.count()
    num_versions.short_description = "#V"

    inlines = [ExtensionVersionAdmin]

admin.site.register(Extension, ExtensionAdmin)
