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
    url(r'^educacao/mapa/$', 'blog.views.educacao_map', name='educacao_map'),
    url(r'^posts/moreposts/$', 'blog.views.query_posts', name='query_posts'),
    url(r'^post/(?P<slug_title>[-\w]+)/$', 'blog.views.post_view', name='post_view'),

    # edit app database (remove, put, change), except system db session, login dt, etc
    url(r'^follower/$', 'blog.views.follower', name='follower'),
    url(r'^post/delete/(?P<oid>\w+)/$', 'blog.views.post_delete', name='post_delete'),
    url(r'^dashboard/post/$', 'blog.views.post_add', name='post_add'),
    url(r'^check_token/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'blog.views.check_token', name='check_token'),

    # ajax paths
    url(r'^oid/(\w+)/$', 'blog.views.ajax_get_post', name='ajax_get_post'),
    url(r'^get/categories/$', 'blog.views.get_categories', name='get_categories'),

    # Apps
    # Feedback 360
    url(r'^feedback360/', include('feedback360.urls')),

    # cleanup rule
    url(r'^(?P<category_anchor>\w+)/$', 'blog.views.category_posts', name='category_posts'),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)