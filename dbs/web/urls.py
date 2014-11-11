from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^tasks/$',    views.task_list),
    url(r'^images/$',   views.image_list),
    url(r'^image/(?P<hash>[a-zA-Z0-9]+)/$', views.image_detail, name="image/detail"),
    url(r'^$',           views.home),
)

