
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('browse',
    url(r'^$', 'views.index', name='ext-index'),
    url(r'^(?P<slug>\w+)', 'views.detail', name='ext-detail'),
)
