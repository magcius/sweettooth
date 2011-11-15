
from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from extensions.models import ExtensionVersion
from review import views

urlpatterns = patterns('',
    url(r'^$', object_list, dict(queryset=ExtensionVersion.objects.locked(),
                                 template_object_name='version',
                                 template_name='review/list.html'),
        name='review-list'),
    url(r'^ajax/get-files/(?P<pk>\d+)', views.ajax_get_files_view, name='review-ajax-files'),
    url(r'^ajax/get-file-list/(?P<pk>\d+)', views.ajax_get_file_list_view, name='review-ajax-file-list'),
    url(r'^ajax/get-file-diff/(?P<pk>\d+)', views.ajax_get_file_diff_view, name='review-ajax-file-diff'),
    url(r'^submit/(?P<pk>\d+)', views.submit_review_view, name='review-submit'),

    url(r'^(?P<pk>\d+)', views.review_version_view, name='review-version'),

)
