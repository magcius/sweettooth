
from django.conf.urls.defaults import patterns, url

from review import views

urlpatterns = patterns('',
    url('^ajax/v/(?P<pk>\d+)', views.AjaxGetFilesView.as_view(), name='review-ajax-files'),
)
