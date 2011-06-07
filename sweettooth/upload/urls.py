
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('upload',
    url(r'^$', 'views.upload_file', name='upload-file'),
    url(r'edit-data/$', 'views.upload_edit_data', name='upload-edit-data'),
)
