
from django.contrib import admin

from errorreports.models import ErrorReport

class ErrorReportAdmin(admin.ModelAdmin):
    list_display = 'user_display', 'extension', 'version_num'
    list_display_links = list_display

    def version_num(self, report):
        return report.version.version

    def extension(self, report):
        return report.version.extension

admin.site.register(ErrorReport, ErrorReportAdmin)
