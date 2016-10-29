import os

from django.conf.urls import patterns, url  
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import user_passes_test, login_required as lr
from django.forms.models import model_to_dict

from . import views
from . import appname

sur = user_passes_test(lambda u:(u.is_superuser or getattr(u, 'perm', None) == appname)) # super_user_required

# menu的合法值由views.ADMIN_KEY 和 views.ORDI_KEY提供
urlpatterns = [
    # app主页暂时由submit_menu代理
    url(r'^$',  lr(views.submit_menu.as_view(menu='报名')), name='home'),
    url(r'^blank_zkz/$',  views.blank_zkz.as_view(menu='打印准考证'), name='blank_zkz'),
    url(r'^config/create/$', sur(views.config_create.as_view(menu='配置')), name='config_create'),
    url(r'^config/update/(?P<pk>\d+)$', sur(views.config_update.as_view(menu='配置')), name='config_update'),
    url(r'^config/detail/(?P<pk>\d+)$', sur(views.config_detail.as_view(menu='配置')), name='config_detail'),
    #url(r'^zkz_all/$', sur(views.zkz_all.as_view(menu='特殊功能')), name='zkz_all'),
]

for name, code in views.ADMIN_MENU:
    urlpatterns.append(
        url(r'^%s/menu/$'%code.split('_')[0],  sur(getattr(views,code).as_view(menu=name)), name=code)
    )

for name, code in views.ORDI_MENU:
    urlpatterns.append(
        url(r'^%s/menu/$'%code.split('_')[0],  getattr(views,code).as_view(menu=name), name=code)
    )


urlpatterns += [
        url(r'^(?P<config_pk>\d+)/create/$', lr(views.create.as_view(menu='报名')),        name='create'), 
        url(r'^(?P<config_pk>\d+)/update/$', lr(views.update.as_view(menu='报名')),        name='update'), 
        url(r'^(?P<config_pk>\d+)/pay/$', lr(views.pay.as_view(menu='缴费')), name='pay'), 
        url(r'^(?P<config_pk>\d+)/detail/$', lr(views.detail.as_view(menu='打印报名表')), name='detail'), 
        url(r'^(?P<config_pk>\d+)/zkz/$',    lr(views.zkz.as_view(menu='打印准考证')),    name='zkz'), 
        url(r'^(?P<config_pk>\d+)/query/$',  lr(views.query.as_view(menu='查询成绩')),     name='query'), 
        url(r'^(?P<config_pk>\d+)/submit/$',  lr(views.submit.as_view(menu='报名')),     name='submit'),
]
                

urlpatterns += [
        url(r'^(?P<config_pk>\d+)/index/$',  sur(views.index.as_view(menu='查看报名情况')), name='index'), 
        url(r'^(?P<config_pk>\d+)/stat/$',   sur(views.stat.as_view(menu='查看报名情况')),  name='stat'), 
        url(r'^(?P<config_pk>\d+)/admin/(?P<query_type>\w+)/$',  sur(views.admin.as_view(menu='管理')),         name='admin'), 
        url(r'^(?P<config_pk>\d+)/admin/detail/(?P<pk>\d+)$', sur(views.admin_detail.as_view(menu='管理')), name='admin_detail'), 
        url(r'^(?P<config_pk>\d+)/admin/zkz/(?P<pk>\d+)$', sur(views.admin_zkz.as_view(menu='管理')), name='admin_zkz'), 
        url(r'^(?P<config_pk>\d+)/write_zkzh/$',  sur(views.write_zkzh.as_view(menu='管理')), name='write_zkzh'), 
        url(r'^(?P<config_pk>\d+)/write_bspm/$',  sur(views.write_bspm.as_view(menu='管理')), name='write_bspm'),               
        url(r'^(?P<config_pk>\d+)/write_zpm/$',  sur(views.write_zpm.as_view(menu='管理')), name='write_zpm'), 
        url(r'^(?P<config_pk>\d+)/download/(?P<field>\w+)/$',  sur(views.download.as_view(menu='管理')), name='download'), 

        url(r'^check_all_alive_zkz/$',  sur(views.check_all_alive_zkz.as_view(menu='所有准考证')), name='check_all_alive_zkz'), 
]
    
