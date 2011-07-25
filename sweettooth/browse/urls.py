
from django.conf.urls.defaults import patterns, url

from extensions.models import Extension
from tagging.views import tagged_object_list

from browse.views import detail, manifest, download, list_ext, browse_tag
from browse.views import modify_tag, upload_screenshot

urlpatterns = patterns('',
    url(r'^$', list_ext, name='ext-index'),

    url(r'tags/(?P<tag>.+)/$', browse_tag, name='ext-browse-tag'),

    url(r'^manifest/(?P<uuid>.+).json$',
        manifest, name='ext-manifest'),

    url(r'^download/(?P<uuid>.+).shell-extension.zip$',
        download, name='ext-download'),

    url(r'ajax/modifytag/(?P<tag>.+)', modify_tag),

    url(r'^extension/(?P<pk>\d+)/(?P<slug>.+)', detail, name='ext-detail'),
    url(r'^extension/(?P<pk>\d+)', detail, dict(slug=None), name='ext-detail'),

    url(r'^extension/upload-screenshot/(?P<pk>\d+)', upload_screenshot, name='upload-screenshot'),
)
