
from django.conf.urls.defaults import patterns, url

from errorreports import views

urlpatterns = patterns('',
    url(r'^report/(?P<pk>\d+)',
        views.ReportErrorView.as_view(), name='errorreports-report'),
)
