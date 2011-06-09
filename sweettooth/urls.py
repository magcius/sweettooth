
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import RedirectView
from django.views import static

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
admin.autodiscover()

from sweettooth.settings import SITE_ROOT

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='/browse'), name='index'),

    url(r'^browse/', include('browse.urls')),

    url(r'^upload/', include('upload.urls')),

    url(r'^uploaded-files/(?P<path>.*)', static.serve,
        dict(document_root=SITE_ROOT), name='uploaded-files'),

    # 'login' and 'register'
    url(r'^', include('auth.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
