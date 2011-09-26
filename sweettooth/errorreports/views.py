
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import DetailView

from errorreports.models import ErrorReport, error_reported
from extensions.models import ExtensionVersion, VISIBLE_STATUSES

class ReportErrorView(DetailView):
    queryset = ExtensionVersion.objects.filter(status__in=VISIBLE_STATUSES)
    context_object_name = "version"
    template_name = "errorreports/report.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.POST['has_errors']:
            errors = request.POST['error']
        else:
            errors = ""

        comment = request.POST['comment']

        if request.user.is_authenticated():
            user, email = request.user, ""
        else:
            user, email = None, request.POST['email']

        report = ErrorReport(version=self.object,
                             comment=comment,
                             errors=errors,
                             user=user,
                             email=email)
        report.save()

        error_reported.send(sender=self, version=self.object, report=report)

        messages.info(request, "Thank you for your error report!")

        return redirect('extensions-version-detail',
                        pk=self.object.pk,
                        ext_pk=self.object.extension.pk,
                        slug=self.object.extension.slug)

class ViewErrorReportView(DetailView):
    model = ErrorReport
    context_object_name = "report"
    template_name = "errorreports/view.html"
