
from django.conf.urls.defaults import patterns, url
from auth.views import AutoFocusAuthenticationForm

urlpatterns = patterns('',
    url(r'login/$', 'django.contrib.auth.views.login',
        dict(template_name='auth/login.html',
             authentication_form=AutoFocusAuthenticationForm), name='auth-login'),
    url(r'logout/$', 'django.contrib.auth.views.logout',
        dict(next_page='/'), name='auth-logout'),
    url(r'register/$', 'auth.views.register', name='auth-register'),
)
