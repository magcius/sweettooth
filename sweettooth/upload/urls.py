
from django.conf.urls.defaults import patterns, url

slug_charset = "[a-zA-Z0-9-_]"

urlpatterns = patterns('upload',
    url(r'^$', 'views.upload_file', dict(slug=None), name='upload-file'),
    url(r'new-version/(?P<slug>%s+)/$' % (slug_charset,), 'views.upload_file', name='upload-file'),
    url(r'edit-data/$', 'views.upload_edit_data', name='upload-edit-data'),
)
