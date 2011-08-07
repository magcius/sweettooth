
import json

from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponse, HttpResponseForbidden, Http404

from review.models import CodeReview
from extensions import models

class AjaxGetFilesView(SingleObjectMixin, View):
    model = models.ExtensionVersion

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            raise Http404()

        if not request.user.has_perm("review.can-review-extensions"):
            return HttpResponseForbidden()

        zipfile = self.object.get_zipfile('r')

        # Currently, we only care about these three files.
        wanted = ('metadata.json', 'extension.js', 'stylesheet.css')

        # filename => file content
        files = {}
        for filename in wanted:
            try:
                files[filename] = zipfile.open(filename, 'r').read()
            except KeyError:
                # File doesn't exist in the zipfile.
                pass

        return HttpResponse(json.dumps(files))
