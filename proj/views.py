import random
from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404,StreamingHttpResponse
from django.forms.models import model_to_dict
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.exceptions import ImproperlyConfigured
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.db.models.query import EmptyQuerySet
from django.contrib.auth.decorators import user_passes_test
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.core.paginator import Paginator, InvalidPage


VIEW_CONTEXT = {
    'STATIC_URL': settings.STATIC_URL,
    'MEDIA_URL': settings.MEDIA_URL,
    'DEBUG':settings.DEBUG,
    'url':lambda view, **kwargs : reverse(view, kwargs=kwargs),
    'static': staticfiles_storage.url,
    'rand': lambda:random.randint(1,100),
    'ICP':getattr(settings, 'ICP', ''), 
    'now':datetime.now,
}

def with_global_context(**kwargs):
    kwargs.update(VIEW_CONTEXT)
    return kwargs

def home(request, template_name='homepage.html'):
    urls = []
    tmp = {}
    for name, dic in settings.XIAN_CONTEXT.items():
        exec('from %s.models import Config'%name, {}, tmp)
        Config = tmp['Config']
        for k, v in Config.memory.items():
            if v.enable:
                action = reverse('%s:submit'%name, args=(v.id,))
                area_url = reverse('%s:submit_menu'%name)
                urls.append((dic['xian_cn'], area_url, v.title, v.url, action))
    return TemplateResponse(request, template_name, 
        with_global_context(xiand=settings.XIAN_CONTEXT,user=request.user, urls = urls))

def guide(request, template_name='guide.html'):
    return TemplateResponse(request, template_name, with_global_context(user=request.user))

def about(request, template_name='about.html'):
    return TemplateResponse(request, template_name, with_global_context(user=request.user))