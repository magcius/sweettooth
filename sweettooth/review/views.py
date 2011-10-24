
try:
    import json
except ImportError:
    import simplejson as json

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

    show_linenum = False

    # filename => { raw, html, filename }
    files = []
    for filename in zipfile.namelist():
        raw = zipfile.open(filename, 'r').read()

        base, extension = os.path.splitext(filename)

        if extension in IMAGE_TYPES:
            mime = IMAGE_TYPES[extension]
            raw_base64 = base64.standard_b64encode(raw)

            html = '<img src="data:%s;base64,%s">' % (mime, raw_base64,)

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

            html = pygments.highlight(raw, lexer, formatter)
            show_linenum = True

        files.append(dict(filename=filename,
                          raw=raw,
                          html=html,
                          show_linenum=show_linenum))

    return files

@post_only_view
@model_view(models.ExtensionVersion)
def change_status_view(request, obj):
    if not can_approve_extension(request.user, obj.extension):
        return HttpResponseForbidden()

    newstatus_string = request.POST.get('newstatus')
    newstatus = dict(Approve=models.STATUS_ACTIVE,
                     Reject=models.STATUS_REJECTED)[newstatus_string]

    log = ChangeStatusLog(user=request.user,
                          version=obj,
                          newstatus=newstatus)
    log.save()

    obj.status = newstatus
    obj.save()

    models.status_changed.send(sender=request, version=obj, log=log)

    return redirect('review-list')

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

    models.reviewed.send(sender=request, version=version, review=review)

    return redirect('review-list')

@model_view(models.ExtensionVersion)
def review_version_view(request, obj):
    extension, version = obj.extension, obj

    # Reviews on previous versions of the same extension.
    previous_versions = CodeReview.objects.filter(version__extension=extension)

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

on_submitted_subject = u"""
GNOME Shell Extensions \N{EM DASH} New review request: "%(name)s", v%(ver)d
""".strip()

on_submitted_template = u"""
A new extension version, "%(name)s", version %(ver)d has been submitted for review by %(creator)s.

Review the extension at %(url)s

\N{EM DASH}

This email was sent automatically by GNOME Shell Extensions. Do not reply.
""".strip()

def send_email_on_submitted(sender, version, **kwargs):
    extension = version.extension

    data = dict(ver=version.version,
                name=extension.name,
                creator=extension.creator,
                url=reverse('review-version', kwargs=dict(pk=version.pk)))

    reviewers = get_all_reviewers().values_list('email', flat=True)

    send_mail(subject=on_submitted_subject % data,
              message=on_submitted_template % data,
              from_email=settings.EMAIL_SENDER,
              recipient_list=reviewers)

models.submitted_for_review.connect(send_email_on_submitted)

on_reviewed_subject = u"""
GNOME Shell Extensions \N{EM DASH} Your extension, "%(name)s", v%(ver)d has been reviewed.
""".strip()

on_reviewed_template = u"""
Your extension, "%(name)s", version %(ver)d has been reviewed. You can see the review here:

%(url)s

Please use the review page to follow up with any comments or concerns.
""".strip()

def send_email_on_reviewed(sender, version, review, **kwargs):
    extension = version.extension

    if review.reviewer == extension.creator:
        # Don't spam the creator with his own review
        return

    data = dict(ver=version.version,
                name=extension.name,
                creator=extension.creator,
                url=reverse('review-version', kwargs=dict(pk=version.pk)))

    send_mail(subject=on_reviewed_subject % data,
              message=on_reviewed_template % data,
              from_email=settings.EMAIL_SENDER,
              recipient_list=[extension.creator.email])

models.reviewed.connect(send_email_on_reviewed)
