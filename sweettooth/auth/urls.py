
from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', dict(template_name='login.html'), name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'register/$', 'auth.views.register', name='register'),
)
