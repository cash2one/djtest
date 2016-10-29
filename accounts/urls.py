from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [
    
    url(r'^$', views.profile, name='profile'),
    url(r'^is_login/$', views.is_login, name='is_login'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^register/$', views.register, name='register'),
    url(r'^register/complete/$', views.register_complete, name='register_complete'),

    url(r'^activate/(?P<activation_key>[a-f0-9]{40})/$', views.activate, name='activate'),
    url(r'^activate/complete/$', views.activate_complete, name='activate_complete'),

    url(r'^password_change/$', views.password_change, name='password_change'),
    url(r'^password_change/done/$', views.password_change_done, name='password_change_done'),

    url(r'^password_reset/$', views.password_reset, name='password_reset'),
    url(r'^password_reset/done/$', views.password_reset_done, name='password_reset_done'),

    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',views.password_reset_confirm, name='password_reset_confirm'),

    url(r'^password_reset/complete/$', views.password_reset_complete, name='password_reset_complete'),
]
 