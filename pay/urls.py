import os

from django.conf.urls import patterns, url  
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import user_passes_test, login_required as lr
from django.forms.models import model_to_dict

from . import views
from . import appname

sur = user_passes_test(lambda u:(u.is_superuser or getattr(u, 'perm', None) == appname)) # super_user_required

urlpatterns = [
    # app主页暂时由submit_menu代理
    # url(r'^$',  lr(views.submit_menu.as_view(menu='报名')), name='home'),
    url(r'^notify/$',  views.notify, name='notify'), 
    url(r'^return/$',  views.return_url_handler, name='return_url_handler'), 
    url(r'^return/success/$',  views.payment_success, name='payment_success'), 
    url(r'^return/error/$',  views.payment_error, name='payment_error'), 
]

    
