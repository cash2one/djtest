import random
from jinja2 import Template

from django.views.generic import View
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404#, StreamingHttpResponse
from django.forms.models import model_to_dict
from django.forms import models as model_forms
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

appname = __file__.replace('\\','/').rsplit('/',2)[1]

class UnproperResponse(HttpResponse):
    temp = Template('''\
<!DOCTYPE html>
<html>
 <head> 
  <meta charset="utf-8" /> 
  <style type="text/css">
      .content {
      text-align:center;
      margin-top:200px;
      font-size:150%;
    }
    p {
      text-align:center;
      font-size:150%;
    }
  </style>
 </head> 

 <body>
    <div class="content"><pre>{{message}}</pre></div>
 </body>
</html>''')
    def __init__(self, message, **kwargs):
        super().__init__(self.temp.render(message=message%kwargs))

class ModelView(View):

    menu = None # 用于HTML侧边条识别页面类型

    model = None # 视图对应哪个model(表)
    form_class = None # 表格
    fields = None # 可选, 表格要显示哪些字段(没有指定form_class时)

    lookup_field = 'pk' # 默认的查询单个对象的字段名(detail, update需要用到)
    lookup_url_kwarg = None # url中查询字段名的关键字,例如/users/(?P<pk>\d)/, 默认和lookup_field一致
    queryset = None # 查询集合, 用于detail和list
    
    prefix = None # 表格前缀
    initial = {} # get表格页面时的初始数据
    template_name = None # 模板路径
    template_name_suffix = None #模板路径的后缀
    context_object_name = None #对象或对象集合的别称,例如model为User时,别称为user或user_list

    paginate_by = None #每页显示多少个对象(记录)
    page_kwarg = 'page' #url中页码字段名的关键字,例如/users/(?P<page>\d+)/

    def get_context_data(self, **kwargs):
        context = {
            # global context
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL' : settings.MEDIA_URL,
            'DEBUG'     : settings.DEBUG,
            'ICP'       : getattr(settings, 'ICP', ''), 
            'url'       : lambda viewname, **kwargs : reverse(viewname, kwargs=kwargs),           
            'static'    : staticfiles_storage.url,
            'rand'      : lambda:random.randint(1,100),
            'appname'   : appname,
            # view specific context
            'user'  : self.request.user,
            'view'  : self,
            'appurl': self.rvs, 
        }
        if getattr(self, 'object', None) is not None:
            context['object'] = self.object
            alias = self.get_context_object_name()
            if alias:
                context[alias] = self.object
        if getattr(self, 'object_list', None) is not None:
            context['object_list'] = self.object_list
            alias = self.get_context_object_name(is_list=True)
            if alias:
                context[alias] = self.object_list
        context.update(kwargs)
        return context

    def error_response(self, message, **kwargs):
        return UnproperResponse(message, **kwargs)

    def rvs(self, name, **kwargs):
        '针对app的reverse'
        return reverse('%s:%s'%(appname, name), kwargs=kwargs)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), **self.get_lookup_dict())

    def get_lookup_dict(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        return {self.lookup_field: self.kwargs[lookup_url_kwarg]}

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset._clone()
        if self.model is not None:
            return self.model._default_manager.all()
        msg = "'%s' 要么定义'queryset'或'model',要么重新get_queryset方法"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    # Form的初始化
    def get_form(self):
        form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class
        if self.model is not None and self.fields is not None:
            return model_forms.modelform_factory(self.model, fields=self.fields)
        msg = "'%s'必须定义form_class属性,或者model和fields属性,或者重写get_form_class方法"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_form_kwargs(self):
        kwargs = {'label_suffix':''}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        else:
            kwargs.update({
                'initial': self.get_initial(),
                'prefix': self.get_prefix(),
            })
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        return kwargs

    def get_initial(self):
        return self.initial.copy()

    def get_prefix(self):
        return self.prefix

    # 页码
    def get_paginate_by(self):
        """
        每页显示多少个对象(记录)
        """
        return self.paginate_by

    def get_paginator(self, queryset, page_size):
        """
        返回一个页码对象
        """
        return Paginator(queryset, page_size)

    def paginate_queryset(self, queryset, page_size):
        """
        根据页码和尺寸返回一个查询集
        """
        paginator = self.get_paginator(queryset, page_size)
        page_number = self.kwargs.get(self.page_kwarg) or \
                      self.request.GET.get(self.page_kwarg) or 1
        try:
            page_number = int(page_number)
        except ValueError:
            if page_number == 'last':
                page_number = paginator.num_pages
            else:
                msg = "页数不是最后一页, 或者不能转换为整数"
                raise Http404(msg)
        try:
            return paginator.page(page_number)
        except InvalidPage as exc:
            msg = '无效页 (%s): %s'
            raise Http404(msg % (page_number, str(exc)))

    # Response rendering
    def get_context_object_name(self, is_list=False):
        """
        返回object或object_list对象的别称
        """
        if self.context_object_name is not None:
            return self.context_object_name
        elif self.model is not None:
            fmt = '%s_list' if is_list else '%s'
            return fmt % self.model._meta.object_name.lower()
        return None

    def get_template_names(self):
        """
        返回模板名称,默认模型是app_label/model_name+template_name_suffix.html
        """
        if self.template_name is not None:
            return [self.template_name]
        if self.model is not None and self.template_name_suffix is not None:
            return ["%s/%s%s.html" % (
                self.model._meta.app_label,
                self.model._meta.object_name.lower(),
                self.template_name_suffix
            )]
        raise ImproperlyConfigured('找不到模板路径')

    def render_to_response(self, context):
        return TemplateResponse(
            request  = self.request,
            template = self.get_template_names(),
            context  = context,
        )

class TemplateView(ModelView):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

class FormView(ModelView):

    success_url = None

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        if self.request.is_ajax():
            data = {'valid':True, 'url':self.get_success_url()}
            return JsonResponse(data)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.is_ajax():
            data = {'valid':False, 'errors':form.errors}
            return JsonResponse(data)
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        if self.success_url is None:
            msg = "'%s' must define 'success_url' or override 'form_valid()'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        return self.success_url 

class DetailView(TemplateView):
    
    template_name_suffix = '_detail'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

class EditView(FormView):

    template_name_suffix = '_form'

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)
        
    def get_success_url(self):
        try:
            return self.success_url or self.object.get_absolute_url()
        except AttributeError:
            msg = "%s必须定义success_url或model对象具有get_absolute_url方法."
            raise ImproperlyConfigured(msg % self.__class__.__name__)

class CreateView(EditView):

    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)

class UpdateView(EditView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(model_to_dict(self.object))
        return initial

class ListView(ModelView):

    template_name_suffix = '_list'
    allow_empty = True

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginate_by = self.get_paginate_by()
        if not self.allow_empty and not queryset.exists():
            raise Http404
        if paginate_by is None:
            # Unpaginated response
            self.object_list = queryset
            context = self.get_context_data(
                page_obj     = None,
                is_paginated = False,
                paginator    = None,
            )
        else:
            # Paginated response
            page = self.paginate_queryset(queryset, paginate_by)
            self.object_list = page.object_list
            context = self.get_context_data(
                page_obj     = page,
                is_paginated = page.has_other_pages(),
                paginator    = page.paginator,
            )
        return self.render_to_response(context)

class DeleteView(ModelView):
    success_url = None
    template_name_suffix = '_delete'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.success_url is None:
            msg = "%s必须定义success_url属性."
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        return self.success_url