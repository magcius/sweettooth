
from django.conf.urls.defaults import patterns, url
from auth import views

urlpatterns = patterns('',
    url(r'^login/', views.login,
        dict(template_name='auth/login.html',
             authentication_form=views.AutoFocusAuthenticationForm), name='auth-login'),

    url(r'^logout/', views.logout,
        dict(next_page='/'), name='auth-logout'),

    url(r'^register/', views.register, name='auth-register'),
    url(r'^profile/(?P<user>.+)', views.profile, name='auth-profile'),
)
