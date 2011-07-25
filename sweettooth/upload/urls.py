
from django.conf.urls.defaults import patterns, url
from upload import views

urlpatterns = patterns('upload',
    url(r'^$', views.upload_file, dict(pk=None), name='upload-file'),
    url(r'new-version/(?P<pk>\d+)/$', views.upload_file, name='upload-file'),
    url(r'edit-data/(?P<pk>\d+)/$', views.upload_edit_data, name='upload-edit-data'),
)
