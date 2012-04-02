
import base64
import os.path

import pygments
import pygments.util
import pygments.lexers
import pygments.formatters

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import redirect, get_object_or_404
from django.template import Context
from django.template.loader import render_to_string
from django.utils.html import escape
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

# Keep this in sync with the BINARY_TYPES list at the top of review.js
BINARY_TYPES = set(['.mo', '.compiled'])

# Stolen from ReviewBoard
# See the top of diffutils.py for details
class NoWrapperHtmlFormatter(pygments.formatters.HtmlFormatter):
    """An HTML Formatter for Pygments that don't wrap items in a div."""

    def _wrap_div(self, inner):
        # Method called by the formatter to wrap the contents of inner.
        # Inner is a list of tuples containing formatted code. If the first item
        # in the tuple is zero, then it's a wrapper, so we should ignore it.
        for tup in inner:
            if tup[0]:
                yield tup

code_formatter = NoWrapperHtmlFormatter(style="borland", cssclass="code")

def can_review_extension(user, extension):
    if user == extension.creator:
        return True

    if user.has_perm("review.can-review-extensions"):
        return True

    return False

def can_approve_extension(user, extension):
    return user.has_perm("review.can-review-extensions")

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

def html_for_file(filename, raw):
    base, extension = os.path.splitext(filename)

    if extension in BINARY_TYPES:
        return None
    elif extension in IMAGE_TYPES:
        mime = IMAGE_TYPES[extension]
        raw_base64 = base64.standard_b64encode(raw)
        return dict(raw=True, html='<img src="data:%s;base64,%s">' % (mime, raw_base64,))
    else:
        return dict(raw=False, lines=split_lines(highlight_file(filename, raw, code_formatter)))

def get_old_version(version, old_version_number):
    extension = version.extension

    if old_version_number is not None:
        old_version = extension.versions.get(version=old_version_number)
    else:
        # Try to get the latest version that's less than the current version
        # that actually has a source field. Sometimes the upload validation
        # fails, so work around it here.
        try:
            old_version = extension.versions.filter(version__lt=version.version).exclude(source="").latest()
        except models.ExtensionVersion.DoesNotExist:
            # There's nothing before us that has a source, or this is the
            # first version.
            return None

    return old_version

def get_zipfiles(version, old_version_number):
    new_zipfile = version.get_zipfile('r')
    old_version = get_old_version(version, old_version_number)

    if old_version is None:
        return None, new_zipfile
    else:
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

def get_fake_chunks(numlines, tag):
    # When a file is added/deleted, we want to show a view where
    # we have nothing in one pane, and a bunch of inserted/delted
    # lines in the other.
    lines = [[n, n, n, [], [], False] for n in range(1, numlines + 1)]
    return [{ 'lines': lines,
              'numlines': numlines,
              'change': tag,
              'collapsable': False,
              'meta': None }]

def get_file_list(zipfile):
    return set(n for n in zipfile.namelist() if not n.endswith('/'))

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_file_list_view(request, obj):
    version, extension = obj, obj.extension

    old_zipfile, new_zipfile = get_zipfiles(version, request.GET.get('oldver', None))

    new_filelist = get_file_list(new_zipfile)

    if old_zipfile is None:
        return dict(unchanged=[],
                    changed=[],
                    added=sorted(new_filelist),
                    deleted=[])

    old_filelist = get_file_list(old_zipfile)

    both    = new_filelist & old_filelist
    added   = new_filelist - old_filelist
    deleted = old_filelist - new_filelist

    unchanged, changed = set([]), set([])

    for filename in both:
        old, new = old_zipfile.open(filename, 'r'), new_zipfile.open(filename, 'r')
        oldcontent, newcontent = old.read(), new.read()

        # Unchanged, remove
        if oldcontent == newcontent:
            unchanged.add(filename)
        else:
            changed.add(filename)

    return dict(unchanged=sorted(unchanged),
                changed=sorted(changed),
                added=sorted(added),
                deleted=sorted(deleted))

@ajax_view
@model_view(models.ExtensionVersion)
def ajax_get_file_diff_view(request, obj):
    version, extension = obj, obj.extension

    filename = request.GET['filename']

    file_base, file_extension = os.path.splitext(filename)
    if file_extension in IMAGE_TYPES:
        return None

    if file_extension in BINARY_TYPES:
        return None

    old_zipfile, new_zipfile = get_zipfiles(version, request.GET.get('oldver', None))

    new_filelist = set(new_zipfile.namelist())
    old_filelist = set(old_zipfile.namelist())

    if filename in old_filelist and filename in new_filelist:
        return get_diff(old_zipfile, new_zipfile, filename)
    elif filename in old_filelist:
        # File was deleted.
        f = old_zipfile.open(filename, 'r')
        lines = split_lines(escape(f.read()))
        f.close()
        return dict(chunks=get_fake_chunks(len(lines), 'delete'), oldlines=lines, newlines=[])
    elif filename in new_filelist:
        # File was added.
        f = new_zipfile.open(filename, 'r')
        lines = split_lines(escape(f.read()))
        f.close()
        return dict(chunks=get_fake_chunks(len(lines), 'insert'), oldlines=[], newlines=lines)
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
    return html_for_file(filename, raw)

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

    status_string = request.POST.get('status')
    newstatus = dict(approve=models.STATUS_ACTIVE,
                     reject=models.STATUS_REJECTED).get(status_string, None)

    if newstatus is not None:
        if newstatus == models.STATUS_ACTIVE and not can_approve_extension(request.user, extension):
            return HttpResponseForbidden()

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

    has_old_version = get_old_version(version, None) is not None
    can_approve = can_approve_extension(request.user, extension)
    can_review = can_review_extension(request.user, extension)

    context = dict(extension=extension,
                   version=version,
                   all_versions=all_versions,
                   previous_reviews=previous_reviews,
                   has_old_version=has_old_version,
                   can_approve=can_approve,
                   can_review=can_review)

    return render(request, 'review/review.html', context)

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

    body = render_to_string('review/submitted_mail.txt', data, Context(autoescape=False)).strip()

    extra_headers = {'X-SweetTooth-Purpose': 'NewExtension',
                     'X-SweetTooth-ExtensionCreator': extension.creator.username}

    message = EmailMessage(subject=subject, body=body, to=reviewers, headers=extra_headers)
    message.send()

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

    body = render_to_string('review/reviewed_mail.txt', data, Context(autoescape=False)).strip()

    recipient_list = list(version.reviews.values_list('reviewer__email', flat=True).distinct())
    recipient_list.append(extension.creator.email)

    if review.reviewer.email in recipient_list:
        # Don't spam the reviewer with his own review.
        recipient_list.remove(review.reviewer.email)

    extra_headers = {'X-SweetTooth-Purpose': 'NewReview',
                     'X-SweetTooth-Reviewer': review.reviewer.username}

    message = EmailMessage(subject=subject, body=body, to=recipient_list, headers=extra_headers)
    message.send()

models.reviewed.connect(send_email_on_reviewed)
