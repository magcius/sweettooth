
from django.conf.urls.defaults import patterns, url

from extensions import views

urlpatterns = patterns('extensions',
    url(r'^manifest/(?P<uuid>.+)\.(?P<ver>\d+)\.json$',
        views.manifest, name='extensions-manifest'),

    url(r'^download/(?P<uuid>.+)\.(?P<ver>\d+)\.shell-extension\.zip$',
        views.download, name='extensions-download'),
)
