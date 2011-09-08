
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView, TemplateView

from extensions import views, models

upload_patterns = patterns('',
    url(r'^$', views.upload_file, dict(pk=None), name='extensions-upload-file'),
    url(r'^new-version/(?P<pk>\d+)/$', views.upload_file, name='extensions-upload-file'),
)

data_patterns = patterns('',
)

ajax_patterns = patterns('',
    url('^i/(?P<pk>\d+)', views.AjaxInlineEditView.as_view(), name='extensions-ajax-inline'),
    url('^l/(?P<pk>\d+)', views.AjaxSubmitAndLockView.as_view(), name='extensions-ajax-submit'),
    url('^us/(?P<pk>\d+)', views.AjaxImageUploadView.as_view(field='screenshot'), name='extensions-ajax-screenshot'),
    url('^ui/(?P<pk>\d+)', views.AjaxImageUploadView.as_view(field='icon'), name='extensions-ajax-icon'),
    url('^d/', views.AjaxDetailsView.as_view(), name='extensions-ajax-details'),
)


urlpatterns = patterns('',
    url(r'^$', ListView.as_view(queryset=models.Extension.objects.visible(),
                                context_object_name="extensions",
                                template_name="extensions/list.html"), name='extensions-index'),

    # we ignore PK of extension, and get extension from version PK
    url(r'^extension/(?P<ext_pk>\d+)/(?P<slug>.+)/version/(?P<pk>\d+)/$',
        views.ExtensionVersionView.as_view(), name='extensions-version-detail'),

    url(r'^extension/(?P<pk>\d+)/(?P<slug>.+)/$',
        views.ExtensionLatestVersionView.as_view(), name='extensions-detail'),
    url(r'^extension/(?P<pk>\d+)/$',
        views.ExtensionLatestVersionView.as_view(), dict(slug=None), name='extensions-detail'),

    url(r'^download-extension/(?P<uuid>.+)\.shell-extension\.zip$',
        views.download, name='extensions-download'),

    url('^upload/', include(upload_patterns)),
    url('^ajax/', include(ajax_patterns)),

    url(r'local/', TemplateView.as_view(template_name="extensions/local.html"), name='extensions-local'),
)
