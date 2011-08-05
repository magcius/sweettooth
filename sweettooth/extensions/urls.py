
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView

from tagging.views import tagged_object_list

from extensions import views, models

upload_patterns = patterns('',
    url(r'^$', views.upload_file, dict(pk=None), name='extensions-upload-file'),
    url(r'^new-version/(?P<pk>\d+)/$', views.upload_file, name='extensions-upload-file'),
)

data_patterns = patterns('',
    url(r'^manifests/(?P<uuid>.+)\.(?P<ver>\d+)\.json$',
        views.manifest, name='extensions-manifest'),

    url(r'^downloads/(?P<uuid>.+)\.(?P<ver>\d+)\.shell-extension\.zip$',
        views.download, name='extensions-download'),
)

ajax_patterns = patterns('',
    url('^i/(?P<pk>\d+)', views.AjaxInlineEditView.as_view(), name='extensions-ajax-inline'),
)


urlpatterns = patterns('',
    url(r'^$', ListView.as_view(queryset=models.Extension.objects.visible(),
                                context_object_name="extensions",
                                template_name="extensions/list.html"), name='extensions-index'),

    url(r'^extensions/tags/(?P<tag>.+)/$', tagged_object_list, name='extensions-tags'),

    # we ignore PK of extension, and get extension from version PK
    url(r'^extension/(?P<ext_pk>\d+)/(?P<slug>.+)/version/(?P<pk>\d+)/$',
        views.ExtensionVersionView.as_view(), name='extensions-version-detail'),

    url(r'^extension/(?P<pk>\d+)/(?P<slug>.+)/$',
        views.ExtensionLatestVersionView.as_view(), name='extensions-detail'),
    url(r'^extension/(?P<pk>\d+)/$',
        views.ExtensionLatestVersionView.as_view(), dict(slug=None), name='extensions-detail'),

    url(r'^extension/upload-screenshot/(?P<pk>\d+)',
        views.upload_screenshot, name='extensions-upload-screenshot'),

    url('^upload/', include(upload_patterns)),
    url('^extension-data/', include(data_patterns)),
    url('^ajax/', include(ajax_patterns)),
)
