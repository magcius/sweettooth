
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('browse',
    url(r'^nagg/', 'views.index'),
)
