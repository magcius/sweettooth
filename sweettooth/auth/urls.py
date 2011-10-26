
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import patterns, url, include
from auth import views, forms
from registration.views import register

urlpatterns = patterns('',
    url(r'^login/', views.login,
        dict(template_name='registration/login.html',
             authentication_form=forms.AuthenticationForm), name='auth-login'),

    url(r'^logout/', views.logout,
        dict(next_page='/'), name='auth-logout'),

    url(r'^register/$', register,
        dict(form_class=forms.AutoFocusRegistrationForm),
        name='registration_register'),

    url(r'settings/(?P<user>.+)', direct_to_template,
        dict(template='registration/settings.html'),
        name='auth-settings'),

    url(r'', include('registration.urls')),
    url(r'^profile/(?P<user>.+)', views.profile, name='auth-profile'),
    url(r'^profile/', views.profile_redirect, name='auth-profile'),
)
