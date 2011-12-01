
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template.loader import render_to_string

from errorreports.models import ErrorReport, error_reported
from errorreports.forms import ErrorReportForm
from extensions.models import Extension

from decorators import post_only_view, model_view
from utils import render

@model_view(Extension.objects.visible())
def report_error_view(request, extension):
    if request.method == 'POST':
        form = ErrorReportForm(data=request.POST)

        if not request.user.is_authenticated():
            return HttpResponseForbidden()

        if form.is_valid():
            report = form.save(request=request, extension=extension)
            error_reported.send(sender=request, request=request,
                                extension=extension, report=report)

            messages.info(request, "Thank you for your error report!")

            return redirect('extensions-detail',
                            pk=extension.pk,
                            slug=extension.slug)

    else:
        form = ErrorReportForm()

    context = dict(extension=extension,
                   form=form)
    return render(request, 'errorreports/report.html', context)

@model_view(ErrorReport)
def view_error_report_view(request, obj):
    return render(request, 'errorreports/view.html', dict(report=obj))


def send_email_on_error_reported(sender, request, extension, report, **kwargs):

    url = request.build_absolute_uri(reverse('errorreports-view',
                                             kwargs=dict(pk=report.pk)))

    data = dict(extension=extension,
                report=report,
                url=url)

    subject = render_to_string('errorreports/report_mail_subject.txt', data).strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('errorreports/report_mail.txt', data).strip()

    send_mail(subject=subject,
              message=message,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[extension.creator.email])

error_reported.connect(send_email_on_error_reported)
