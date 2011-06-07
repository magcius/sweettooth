
from django.conf.urls.defaults import patterns, url
from auth.views import AutoFocusAuthenticationForm

urlpatterns = patterns('',
    url(r'login/$', 'django.contrib.auth.views.login',
        dict(template_name='login.html',
             authentication_form=AutoFocusAuthenticationForm), name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout',
        dict(next_page='/'), name='logout'),
    url(r'register/$', 'auth.views.register', name='register'),
)
