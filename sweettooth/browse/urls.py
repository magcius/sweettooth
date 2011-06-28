
from django.conf.urls.defaults import patterns, url

from extensions.models import Extension
from tagging.views import tagged_object_list

from browse.views import detail, manifest, download, list_ext

slug_charset = "[a-zA-Z0-9-_]"

urlpatterns = patterns('',
    url(r'^$', list_ext, name='ext-index'),

    url(r'tags/(?P<tag>%s+)/$' % (slug_charset,), tagged_object_list,
        dict(queryset_or_model=Extension,
             template_object_name="extensions",
             template_name="list.html"), name='ext-tags'),

    url(r'^manifest/(?P<uuid>.+).json$',
        manifest, name='ext-manifest'),

    url(r'^download/(?P<uuid>.+).shell-extension.zip$',
        download, name='ext-download'),

    url(r'^extension/(?P<slug>%s+)/$' % (slug_charset,), detail,
        dict(ver=None), name='ext-detail'),
    url(r'^extension/(?P<slug>%s+)/(?P<ver>\d+)/$' % (slug_charset,), detail),

)
