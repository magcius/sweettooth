
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template.loader import render_to_string

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


def send_email_on_error_reported(request, version, report, **kwargs):
    extension = version.extension

    url = request.build_absolute_uri(reverse('errorreports-view',
                                             kwargs=dict(pk=report.pk)))

    data = dict(version=version,
                extension=extension,
                report=report,
                url=url)

    subject = render_to_string('errorreports/report_mail_subject.txt', data).strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('errorreports/report_mail.txt', data).strip()

    send_mail(subject=subject,
              message=message,
              from_email=settings.EMAIL_SENDER,
              recipient_list=[extension.creator.email])

error_reported.connect(send_email_on_error_reported)
