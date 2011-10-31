
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from errorreports.models import ErrorReport, error_reported
from extensions.models import ExtensionVersion

from decorators import post_only_view, model_view
from utils import render

@model_view(ExtensionVersion.objects.visible())
def report_error_view(request, obj):
    extension, version = obj.extension, obj

    if request.method == 'POST':
        comment = request.POST['comment']

        if not request.user.is_authenticated():
            return HttpResponseForbidden()

        report = ErrorReport(version=version,
                             comment=comment,
                             user=request.user)
        report.save()

        error_reported.send(sender=request, version=version, report=report)

        messages.info(request, "Thank you for your error report!")

        return redirect('extensions-version-detail',
                        pk=version.pk,
                        ext_pk=extension.pk,
                        slug=extension.slug)

    else:
        context = dict(version=version,
                       extension=extension)
        return render(request, 'errorreports/report.html', context)

@model_view(ErrorReport)
def view_error_report_view(request, obj):
    return render(request, 'errorreports/view.html', dict(report=obj))
