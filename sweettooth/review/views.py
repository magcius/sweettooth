
import json
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.utils.safestring import mark_safe

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
