
from django.contrib import admin

from errorreports.models import ErrorReport

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
