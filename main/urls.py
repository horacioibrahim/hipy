from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'blog.views.index', name='homepage'),
    url(r'^login/$', 'blog.views.my_login', name='my_login'),
    url(r'^logout/$', 'blog.views.my_logout', name='my_logout'),
    url(r'^dashboard/post/$', 'blog.views.post_add', name='post_add'),
    url(r'^get/categories/$', 'blog.views.get_categories', name='get_categories'),
    url(r'^follower/$', 'blog.views.follower', name='follower'),
    url(r'^post/delete/(?P<oid>\w+)/$', 'blog.views.post_delete', name='post_delete'),
    url(r'^post/(?P<slug_title>[-\w]+)/$', 'blog.views.post_view', name='post_view'),
    url(r'^oid/(\w+)/$', 'blog.views.ajax_get_post', name='ajax_get_post'),
    url(r'^(?P<category_anchor>\w+)/$', 'blog.views.category_posts', name='category_posts'),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)