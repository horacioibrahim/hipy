from django.conf.urls import patterns, url


urlpatterns = patterns('feedback360.views',
    url(r'^$', 'home', name='feedback360_home'),
    url(r'^home/$', 'home', name='feedback360_home'),
    url(r'^access/$', 'access_control', name='access_control'),
    url(r'^remove/$', 'remove_from_facebook', name='remove_from_facebook'),
    url(r'^invitation/add/$', 'add_invite', name='add_invite'),
    url(r'^invitation/del/$', 'del_invite', name='del_invite'),
    url(r'^replies/$', 'replies', name='replies'),
    url(r'^replies/thanks/$', 'thanks_for_replies',
                                            name='thanks_replies'),
    url(r'^asks/add/$', 'add_ask', name='add_ask'),
    url(r'^asks/del/(?P<pk>\w+)/$', 'del_ask', name='del_ask'),

)