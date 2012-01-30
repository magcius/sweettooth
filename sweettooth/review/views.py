
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
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import redirect, get_object_or_404
from django.template import Context
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils import simplejson as json
from django.views.decorators.http import require_POST

from review.diffutils import get_chunks, split_lines
from review.models import CodeReview, ChangeStatusLog, get_all_reviewers
from extensions import models

from decorators import ajax_view, model_view
from utils import render

IMAGE_TYPES = {
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif':  'image/gif',
    '.bmp':  'image/bmp',
    '.svg':  'image/svg+xml',
}

BINARY_TYPES = set(['.mo', '.png', ',jpg', '.jpeg', '.gif', '.bmp'])

code_formatter = pygments.formatters.HtmlFormatter(style="borland", cssclass="code")

def get_filelist(zipfile, disallow_binary):
    for name in zipfile.namelist():
        if name.endswith('/'):
            # There's no directory flag in the info, so I'm
            # guessing this is the most reliable way to do it.
            continue

        if disallow_binary:
            base, extension = os.path.splitext(name)
            if extension in BINARY_TYPES:
                continue

        yield name

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

def highlight_file(filename, raw, formatter):
    try:
        lexer = pygments.lexers.guess_lexer_for_filename(filename, raw)
    except pygments.util.ClassNotFound:
        # released pygments doesn't yet have .json
        # so hack around it here.
        if filename.endswith('.json'):
            lexer = pygments.lexers.get_lexer_by_name('js')
        else:
            lexer = pygments.lexers.get_lexer_by_name('text')

    return pygments.highlight(raw, lexer, formatter)

def html_for_file(filename, version, raw):
    base, extension = os.path.splitext(filename)

    if extension in IMAGE_TYPES:
        mime = IMAGE_TYPES[extension]
        raw_base64 = base64.standard_b64encode(raw)

        return dict(html='<img src="data:%s;base64,%s">' % (mime, raw_base64,),
                    num_lines=0)

    elif extension in BINARY_TYPES:
        download_url = reverse('review-download', kwargs=dict(pk=version.pk))
        html = "<p>This file is binary. Please <a href=\"%s\">" \
            "download the zipfile</a> to see it.</p>" % (download_url,)

        return dict(html=html, num_lines=0)
    else:
        return dict(html=highlight_file(filename, raw, code_formatter),
                    num_lines=len(raw.strip().splitlines()))

def get_zipfiles(version, old_version_number=None):
    extension = version.extension

    new_zipfile = version.get_zipfile('r')
    if version.version == 1:
        return None, new_zipfile

    if old_version_number is None:
        old_version_number = version.version - 1

    old_version = extension.versions.get(version=old_version_number)
    old_zipfile = old_version.get_zipfile('r')

    return old_zipfile, new_zipfile

def get_diff(old_zipfile, new_zipfile, filename):
    old, new = old_zipfile.open(filename, 'r'), new_zipfile.open(filename, 'r')
    oldcontent, newcontent = old.read(), new.read()

    if oldcontent == newcontent:
        return None

    old.close()
    new.close()

    oldmarkup = escape(oldcontent)
    newmarkup = escape(newcontent)

    oldlines = split_lines(oldmarkup)
    newlines = split_lines(newmarkup)

    chunks = list(get_chunks(oldlines, newlines))
    return dict(chunks=chunks,
                oldlines=oldlines,
                newlines=newlines)

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_file_list_view(request, obj):
    version, extension = obj, obj.extension

    old_version_number = request.GET.get('oldver', None)

    old_zipfile, new_zipfile = get_zipfiles(version, old_version_number)

    disallow_binary = json.loads(request.GET['disallow_binary'])

    new_filelist = set(get_filelist(new_zipfile, disallow_binary))

    if old_zipfile is None:
        return dict(both=[],
                    added=sorted(new_filelist),
                    deleted=[])

    old_filelist = set(get_filelist(old_zipfile, disallow_binary))

    both    = new_filelist & old_filelist
    added   = new_filelist - old_filelist
    deleted = old_filelist - new_filelist

    return dict(both=sorted(both),
                added=sorted(added),
                deleted=sorted(deleted))

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_file_diff_view(request, obj):
    version, extension = obj, obj.extension

    filename = request.GET['filename']
    old_version_number = request.GET.get('oldver', None)

    file_base, file_extension = os.path.splitext(filename)
    if file_extension in IMAGE_TYPES:
        return None

    if file_extension in BINARY_TYPES:
        return None

    old_zipfile, new_zipfile = get_zipfiles(version, old_version_number)

    new_filelist = set(new_zipfile.namelist())
    old_filelist = set(old_zipfile.namelist())

    if filename in old_filelist and filename in new_filelist:
        return get_diff(old_zipfile, new_zipfile, filename)
    else:
        return None

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_file_view(request, obj):
    zipfile = obj.get_zipfile('r')
    filename = request.GET['filename']

    try:
        f = zipfile.open(filename, 'r')
    except KeyError:
        raise Http404()

    raw = f.read()
    return html_for_file(filename, obj, raw)

def download_zipfile(request, pk):
    version = get_object_or_404(models.ExtensionVersion, pk=pk)

    if version.status == models.STATUS_NEW:
        return HttpResponseForbidden()

    return redirect(version.source.url)

@require_POST
@model_view(models.ExtensionVersion)
def submit_review_view(request, obj):
    extension, version = obj.extension, obj

    if not can_review_extension(request.user, extension):
        return HttpResponseForbidden()

    review = CodeReview(version=version,
                        reviewer=request.user,
                        comments=request.POST.get('comments'))

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

            review.changelog = log

            models.status_changed.send(sender=request, version=obj, log=log)

    review.save()

    models.reviewed.send(sender=request, request=request,
                         version=version, review=review)

    return redirect('review-list')

@model_view(models.ExtensionVersion)
def review_version_view(request, obj):
    extension, version = obj.extension, obj

    # Reviews on all versions of the same extension.
    all_versions = extension.versions.order_by('-version')

    # Other reviews on the same version.
    previous_reviews = version.reviews.all()

    can_approve = can_approve_extension(request.user, extension)

    context = dict(extension=extension,
                   version=version,
                   all_versions=all_versions,
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

    subject = render_to_string('review/submitted_mail_subject.txt', data, Context(autoescape=False))
    subject = subject.strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('review/submitted_mail.txt', data, Context(autoescape=False)).strip()

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
                review=review,
                url=url)

    subject = render_to_string('review/reviewed_mail_subject.txt', data, Context(autoescape=False))
    subject = subject.strip()
    subject = subject.replace('\n', '')
    subject = subject.replace('\r', '')

    message = render_to_string('review/reviewed_mail.txt', data, Context(autoescape=False)).strip()

    recipient_list = list(version.reviews.values_list('reviewer__email', flat=True).distinct())
    recipient_list.append(extension.creator.email)

    if review.reviewer.email in recipient_list:
        # Don't spam the reviewer with his own review.
        recipient_list.remove(review.reviewer.email)

    send_mail(subject=subject,
              message=message,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=recipient_list)

models.reviewed.connect(send_email_on_reviewed)
