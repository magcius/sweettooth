
from django.conf.urls.defaults import patterns, url

from extensions.models import Extension
from tagging.views import tagged_object_list

from browse.views import detail, manifest, download, list_ext, browse_tag, modify_tag

slug_charset = "[a-zA-Z0-9-_]"

urlpatterns = patterns('',
    url(r'^$', list_ext, name='ext-index'),

    url(r'tags/(?P<tag>%s+)/$' % (slug_charset,), browse_tag, name='ext-browse-tag'),

    url(r'^manifest/(?P<uuid>.+).json$',
        manifest, name='ext-manifest'),

    url(r'^download/(?P<uuid>.+).shell-extension.zip$',
        download, name='ext-download'),

    url(r'ajax/modifytag/(?P<tag>%s+)' % (slug_charset,), modify_tag),

    url(r'^extension/(?P<slug>%s+)/$' % (slug_charset,), detail,
        dict(ver=None), name='ext-detail'),
    url(r'^extension/(?P<slug>%s+)/(?P<ver>\d+)/$' % (slug_charset,), detail),

)
