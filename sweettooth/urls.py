
from django.conf.urls.defaults import patterns, include, url

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
admin.autodiscover()

from sweettooth.settings import SITE_ROOT

urlpatterns = patterns('',
    url(r'^upload/', include('upload.urls')),

    # dummy URI for reverse()
    url(r'^static/extension-data/(?P<filepath>.+)', lambda x: None,
        name='ext-url'),

    # 'login' and 'register'
    url(r'^', include('auth.urls')),
    url(r'^', include('browse.urls'), name='index'),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^comments/', include('django.contrib.comments.urls')),
)

urlpatterns += staticfiles_urlpatterns()
