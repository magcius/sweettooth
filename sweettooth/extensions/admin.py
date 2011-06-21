
from django.contrib import admin
from extensions.models import Extension, ExtensionVersion

class ExtensionVersionAdmin(admin.TabularInline):
    model = ExtensionVersion
    list_display = 'version', 'source'

class ExtensionAdmin(admin.ModelAdmin):
    list_display = 'is_published', 'name', 'num_versions', 'creator'
    list_display_links = 'name',

    def num_versions(self, ext):
        return ext.extensionversion_set.count()
    num_versions.short_description = "#V"

    inlines = [ExtensionVersionAdmin]

admin.site.register(Extension, ExtensionAdmin)
