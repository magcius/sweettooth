
from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

from extensions import views, models

upload_patterns = patterns('',
    url(r'^$', views.upload_file, dict(pk=None), name='extensions-upload-file'),
    url(r'^new-version/(?P<pk>\d+)/$', views.upload_file, name='extensions-upload-file'),
)

ajax_patterns = patterns('',
    url(r'^edit/(?P<pk>\d+)', views.ajax_inline_edit_view, name='extensions-ajax-inline'),
    url(r'^submit/(?P<pk>\d+)', views.ajax_submit_and_lock_view, name='extensions-ajax-submit'),
    url(r'^upload/screenshot/(?P<pk>\d+)', views.ajax_image_upload_view(field='screenshot'), name='extensions-ajax-screenshot'),
    url(r'^upload/icon/(?P<pk>\d+)', views.ajax_image_upload_view(field='icon'), name='extensions-ajax-icon'),
    url(r'^detail/', views.ajax_details_view, name='extensions-ajax-details'),
)

shell_patterns = patterns('',
    url(r'^extension-info/', views.ajax_details_view),

    url(r'^download-extension/(?P<uuid>.+)\.shell-extension\.zip$',
        views.download),
)

urlpatterns = patterns('',
    url(r'^$', object_list, dict(queryset=models.Extension.objects.visible(),
                                 template_object_name='extension',
                                 template_name='extensions/list.html'),
        name='extensions-index'),

    # we ignore PK of extension, and get extension from version PK
    url(r'^extension/(?P<ext_pk>\d+)/(?P<slug>.+)/version/(?P<pk>\d+)/$',
        views.extension_version_view, name='extensions-version-detail'),

    url(r'^extension/(?P<pk>\d+)/(?P<slug>.+)/$',
        views.extension_latest_version_view, name='extensions-detail'),
    url(r'^extension/(?P<pk>\d+)/$',
        views.extension_latest_version_view, dict(slug=None), name='extensions-detail'),

    url(r'^local/', direct_to_template, dict(template='extensions/local.html'), name='extensions-local'),

    url(r'^upload/', include(upload_patterns)),
    url(r'^ajax/', include(ajax_patterns)),
    url(r'', include(shell_patterns)),
)
