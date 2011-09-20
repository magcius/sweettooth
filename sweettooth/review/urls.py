
from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView

from review import views
from extensions.models import ExtensionVersion, STATUS_LOCKED

urlpatterns = patterns('',
    url(r'^$', ListView.as_view(queryset=ExtensionVersion.objects.filter(status=STATUS_LOCKED),
                                context_object_name="versions",
                                template_name="review/list.html"), name='review-list'),

    url(r'^ajax/v/(?P<pk>\d+)', views.AjaxGetFilesView.as_view(), name='review-ajax-files'),
    url(r'^submit/(?P<pk>\d+)', views.SubmitReviewView.as_view(), name='review-submit'),
    url(r'^(?P<pk>\d+)', views.ReviewVersionView.as_view(), name='review-version'),
)
