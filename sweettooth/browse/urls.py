
from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from extensions.models import Extension
from tagging.views import tagged_object_list

urlpatterns = patterns('browse',
    url(r'^$', object_list,
        dict(queryset=Extension.objects.all(),
             template_object_name="extensions",
             template_name="list.html"), name='ext-index'),
    url(r'tags/(?P<tag>\w+)', tagged_object_list,
        dict(queryset_or_model=Extension,
             template_object_name="extensions",
             template_name="list.html"), name='ext-tags',),
    url(r'^(?P<slug>\w+)', 'views.detail', name='ext-detail'),
)
