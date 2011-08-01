
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.views import static
admin.autodiscover()

from sweettooth.settings import SITE_ROOT

urlpatterns = patterns('',
    url(r'^upload/', include('upload.urls')),
    url(r'^extensions/', include('extensions.urls')),

    # 'login' and 'register'
    url(r'^', include('auth.urls')),
    url(r'^', include('browse.urls'), name='index'),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^comments/', include('django.contrib.comments.urls')),
)

if settings.DEBUG:
    # Use static.serve for development...
    urlpatterns += url(r'^static/extension-data/(?P<path>.*)', static.serve,
                       dict(document_root=settings.MEDIA_ROOT), name='extension-data'),
else:
    # and a dummy to reverse on for production.
    urlpatterns += url(r'^static/extension-data/(?P<path>.*)', lambda n: None,
                       name='extension-data'),


urlpatterns += staticfiles_urlpatterns()
