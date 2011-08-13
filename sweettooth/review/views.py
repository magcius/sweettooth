
try:
    import json
except ImportError:
    import simplejson as json

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from django.views.generic import View, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.shortcuts import redirect

from review.models import CodeReview
from extensions import models

class AjaxGetFilesView(SingleObjectMixin, View):
    model = models.ExtensionVersion
    formatter = HtmlFormatter(style="borland", cssclass="code")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            raise Http404()

        if not request.user.has_perm("review.can-review-extensions"):
            return HttpResponseForbidden()

        zipfile = self.object.get_zipfile('r')

        # Currently, we only care about these three files.
        wanted = (('metadata.json', 'js'), ('extension.js', 'js'), ('stylesheet.css', 'css'))

        # filename => { raw, html, filename }
        files = []
        for filename, lexer in wanted:
            try:
                raw = zipfile.open(filename, 'r').read()
                html = highlight(raw, get_lexer_by_name(lexer), self.formatter)

                files.append(dict(filename=filename, raw=raw, html=html))
            except KeyError:
                # File doesn't exist in the zipfile.
                pass

        return HttpResponse(mark_safe(json.dumps(files)),
                            content_type="application/json")

class SubmitReviewView(SingleObjectMixin, View):
    model = models.ExtensionVersion

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.has_perm("review.can-review-extensions"):
            return HttpResponseForbidden()

        if self.object.status != models.STATUS_LOCKED:
            return HttpResponseForbidden()

        newstatus = request.POST.get('newstatus')
        statuses = dict(Accept=models.STATUS_ACTIVE,
                        Reject=models.STATUS_REJECTED)

        if newstatus not in statuses:
            return HttpResponseForbidden()

        self.object.status = statuses[newstatus]
        self.object.save()

        review = CodeReview(version=self.object,
                            reviewer=request.user,
                            comments=request.POST.get('comments'),
                            newstatus=self.object.status)
        review.save()

        models.reviewed.send(sender=self, version=self.object, review=review)

        verb_past_progressive = dict(Accept="accepted",
                                     Reject="rejected")[newstatus]

        messages.info(request, "The extension was successfully %s. Thanks!" % (verb_past_progressive,))
        return redirect('review-list')

class ReviewVersionView(DetailView):
    model = models.ExtensionVersion
    template_name = "review/review.html"
    context_object_name = "version"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.has_perm("review.can-review-extensions"):
            return HttpResponseForbidden()

        if self.object.status != models.STATUS_LOCKED:
            return HttpResponseForbidden()

        return super(ReviewVersionView, self).get(request, *args, **kwargs)
