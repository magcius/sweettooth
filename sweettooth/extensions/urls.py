
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView, TemplateView, DetailView

from extensions import views, models

upload_patterns = patterns('',
    url(r'^$', views.upload_file, dict(pk=None), name='extensions-upload-file'),
    url(r'^new-version/(?P<pk>\d+)/$', views.upload_file, name='extensions-upload-file'),
)

ajax_patterns = patterns('',
    url(r'^i/(?P<pk>\d+)', views.AjaxInlineEditView.as_view(), name='extensions-ajax-inline'),
    url(r'^l/(?P<pk>\d+)', views.AjaxSubmitAndLockView.as_view(), name='extensions-ajax-submit'),
    url(r'^us/(?P<pk>\d+)', views.AjaxImageUploadView.as_view(field='screenshot'), name='extensions-ajax-screenshot'),
    url(r'^ui/(?P<pk>\d+)', views.AjaxImageUploadView.as_view(field='icon'), name='extensions-ajax-icon'),
    url(r'^d/', views.AjaxDetailsView.as_view(), name='extensions-ajax-details'),
)

shell_patterns = patterns('',
    url(r'^extension-info/', views.AjaxDetailsView.as_view()),

    url(r'^download-extension/(?P<uuid>.+)\.shell-extension\.zip$',
        views.download),
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

    url(r'^upload/', include(upload_patterns)),
    url(r'^ajax/', include(ajax_patterns)),
    url(r'', include(shell_patterns)),

    url(r'local/', TemplateView.as_view(template_name="extensions/local.html"), name='extensions-local'),

    url(r'^error-report/(?P<pk>\d+)',
        DetailView.as_view(model=models.ExtensionVersion,
                           context_object_name="version",
                           template_name="extensions/error-report.html"), name='extensions-error'),
)
