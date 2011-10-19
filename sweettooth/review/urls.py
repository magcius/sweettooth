
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
    url(r'^submit/(?P<pk>\d+)', views.submit_review_view, name='review-submit'),
    url(r'^approve/(?P<pk>\d+)', views.change_status_view, name='review-approve'),

    url(r'^(?P<pk>\d+)', views.review_version_view, name='review-version'),

)
