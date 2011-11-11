
import base64
import os.path

import pygments
import pygments.util
import pygments.lexers
import pygments.formatters

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template.loader import render_to_string

from review.models import CodeReview, ChangeStatusLog, get_all_reviewers
from extensions import models

from decorators import ajax_view, model_view, post_only_view
from utils import render

IMAGE_TYPES = {
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif':  'image/gif',
    '.bmp':  'image/bmp',
    '.svg':  'image/svg+xml',
}

def can_review_extension(user, extension):
    if user == extension.creator:
        return True

    if user.has_perm("review.can-review-extensions"):
        return True

    return False

def can_approve_extension(user, extension):
    if user.is_superuser:
        return True

    if user.has_perm("review.can-review-extensions"):
        return user != extension.creator

    return False

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_files_view(request, obj):
    formatter = pygments.formatters.HtmlFormatter(style="borland", cssclass="code")

    if not can_review_extension(request.user, obj.extension):
        return HttpResponseForbidden()

    zipfile = obj.get_zipfile('r')

    # filename => { raw, html, filename }
    files = []
    for filename in sorted(zipfile.namelist()):
        raw = zipfile.open(filename, 'r').read()

        base, extension = os.path.splitext(filename)

        file_ = dict(filename=filename)

        if extension in IMAGE_TYPES:
            mime = IMAGE_TYPES[extension]
            raw_base64 = base64.standard_b64encode(raw)

            file_.update(html='<img src="data:%s;base64,%s">' % (mime, raw_base64,),
                         num_lines=0)

        else:
            try:
                lexer = pygments.lexers.guess_lexer_for_filename(filename, raw)
            except pygments.util.ClassNotFound:
                # released pygments doesn't yet have .json
                # so hack around it here.
                if filename.endswith('.json'):
                    lexer = pygments.lexers.get_lexer_by_name('js')
                else:
                    lexer = pygments.lexers.get_lexer_by_name('text')

            file_.update(html=pygments.highlight(raw, lexer, formatter),
                         num_lines=len(raw.strip().splitlines()))

        files.append(file_)

    return files

@post_only_view
@model_view(models.ExtensionVersion)
def submit_review_view(request, obj):
    extension, version = obj.extension, obj

    if not can_review_extension(request.user, extension):
        return HttpResponseForbidden()

    review = CodeReview(version=version,
                        reviewer=request.user,
                        comments=request.POST.get('comments'))
    review.save()

    messages.info(request, "Thank you for reviewing %s" % (extension.name,))

    if can_approve_extension(request.user, obj.extension):
        status_string = request.POST.get('status')
        newstatus = dict(approve=models.STATUS_ACTIVE,
                         reject=models.STATUS_REJECTED).get(status_string, None)

        if newstatus is not None:
            log = ChangeStatusLog(user=request.user,
                                  version=obj,
                                  newstatus=newstatus)
            log.save()

            obj.status = newstatus
            obj.save()

            models.status_changed.send(sender=request, version=obj, log=log)

    models.reviewed.send(sender=request, request=request,
                         version=version, review=review)

    return redirect('review-list')

@model_view(models.ExtensionVersion)
def review_version_view(request, obj):
    extension, version = obj.extension, obj

    # Reviews on previous versions of the same extension.
    previous_versions = extension.versions.order_by('-version')

    # Exclude this version...
    previous_versions = previous_versions.exclude(version=version.version)


    # Other reviews on the same version
    previous_reviews = version.reviews.all()

    can_approve = can_approve_extension(request.user, extension)

    context = dict(extension=extension,
                   version=version,
                   previous_versions=previous_versions,
                   previous_reviews=previous_reviews,
                   can_approve=can_approve)

    if can_review_extension(request.user, extension):
        template_name = "review/review_reviewer.html"
    else:
        template_name = "review/review.html"

    return render(request, template_name, context)

def send_email_on_submitted(sender, request, version, **kwargs):
    extension = version.extension

    url = request.build_absolute_uri(reverse('review-version',
                                             kwargs=dict(pk=version.pk)))

    data = dict(version=version,
                extension=extension,
                url=url)

    reviewers = get_all_reviewers().values_list('email', flat=True)

    subject = render_to_string('review/submitted_mail_subject.txt', data).strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('review/submitted_mail.txt', data).strip()

    send_mail(subject=subject,
              message=message,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=reviewers)

models.submitted_for_review.connect(send_email_on_submitted)

def send_email_on_reviewed(sender, request, version, review, **kwargs):
    extension = version.extension

    url = request.build_absolute_uri(reverse('review-version',
                                             kwargs=dict(pk=version.pk)))

    data = dict(version=version,
                extension=extension,
                url=url)

    subject = render_to_string('review/reviewed_mail_subject.txt', data).strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('review/reviewed_mail.txt', data).strip()

    recipient_list = list(version.reviews.values_list('reviewer__email', flat=True).distinct())
    recipient_list.append(extension.creator)

    if review.reviewer.email in recipient_list:
        # Don't spam the reviewer with his own review.
        recipient_list.remove(review.reviewer.email)

    send_mail(subject=subject,
              message=message,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=recipient_list)

models.reviewed.connect(send_email_on_reviewed)
