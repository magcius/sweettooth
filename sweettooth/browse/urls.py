
from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from extensions.models import Extension
from tagging.views import tagged_object_list

from browse.views import extension_detail, extension_download

slug_charset = "[a-zA-Z0-9-_]"

urlpatterns = patterns('browse',
    url(r'^$', object_list,
        dict(queryset=Extension.objects.filter(is_published=True),
             template_object_name="extensions",
             template_name="list.html"), name='ext-index'),
    url(r'tags/(?P<tag>%s+)' % (slug_charset,), tagged_object_list,
        dict(queryset_or_model=Extension,
             template_object_name="extensions",
             template_name="list.html"), name='ext-tags'),

    url(r'^download/(?P<slug>%s+)/(?P<ver>\d+)' % (slug_charset,),
        extension_download, name='ext-download'),

    url(r'^(?P<slug>%s+)' % (slug_charset,), extension_detail,
        dict(ver='latest'), name='ext-detail'),
    url(r'^(?P<slug>%s+)/(?P<ver>\d+)' % (slug_charset,), extension_detail),
)
