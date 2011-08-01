
from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView

from extensions.models import Extension
from tagging.views import tagged_object_list

from browse.views import ExtensionLatestVersionView, ExtensionVersionView
from browse.views import modify_tag, upload_screenshot

urlpatterns = patterns('',
    url(r'^$', ListView.as_view(model=Extension,
                                context_object_name="extensions",
                                template_name="browse/list.html"), name='browse-index'),

    url(r'tags/(?P<tag>.+)/$', tagged_object_list, name='browse-tags'),

    url(r'ajax/modifytag/(?P<tag>.+)', modify_tag),

    url(r'^extension/(?P<pk>\d+)/(?P<slug>.+)',
        ExtensionLatestVersionView.as_view(), name='browse-detail'),
    url(r'^extension/(?P<pk>\d+)/',
        ExtensionLatestVersionView.as_view(), dict(slug=None), name='browse-detail'),

    # we ignore PK of extension, and get extension from version PK
    url(r'^extension/(?P<fake_pk>\d+)/(?P<slug>.+)/version/(?P<pk>\d+)/',
        ExtensionVersionView.as_view(), name='browse-version-detail'),

    url(r'^extension/upload-screenshot/(?P<pk>\d+)', upload_screenshot, name='browse-upload-screenshot'),
)
