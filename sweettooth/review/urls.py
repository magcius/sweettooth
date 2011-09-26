
from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView

from review import views

urlpatterns = patterns('',
    url(r'^$', views.ReviewListView.as_view(), name='review-list'),
    url(r'^ajax/get-files/(?P<pk>\d+)', views.AjaxGetFilesView.as_view(), name='review-ajax-files'),
    url(r'^submit/(?P<pk>\d+)', views.SubmitReviewView.as_view(), name='review-submit'),
    url(r'^(?P<pk>\d+)', views.ReviewVersionView.as_view(), name='review-version'),
)
