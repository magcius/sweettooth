
from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin

from extensions.models import Extension, ExtensionVersion, ErrorReport
from review.models import CodeReview

class CodeReviewAdmin(admin.TabularInline):
    model = CodeReview
    fields = 'reviewer', 'comments',

class ExtensionVersionAdmin(admin.ModelAdmin):
    list_display = 'title', 'status',
    list_display_links = 'title',

    def title(self, ver):
        return "%s (%d)" % (ver.extension.uuid, ver.version)
    title.short_description = "Extension (version)"

    inlines = [CodeReviewAdmin]

admin.site.register(ExtensionVersion, ExtensionVersionAdmin)

class ExtensionVersionInline(admin.TabularInline):
    model = ExtensionVersion
    fields = 'version', 'status',
    extra = 0

class ExtensionAdmin(admin.ModelAdmin):
    list_display = 'name', 'num_versions', 'creator',
    list_display_links = 'name',

    def num_versions(self, ext):
        return ext.versions.count()
    num_versions.short_description = "#V"

    inlines = [ExtensionVersionInline]

admin.site.register(Extension, ExtensionAdmin)

class ErrorReportAdmin(admin.ModelAdmin):
    list_display = 'user_or_email', 'extension', 'version_num'
    list_display_links = list_display

    def user_or_email(self, report):
        if report.user:
            return report.user
        else:
            return report.email

    def version_num(self, report):
        return report.version.version

    def extension(self, report):
        return report.version.extension

admin.site.register(ErrorReport, ErrorReportAdmin)
