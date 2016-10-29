import xlwt
from datetime import datetime, timedelta
from collections import OrderedDict

from django.views.generic import View
from django.utils.timezone import localtime
from django.template.response import TemplateResponse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from django.forms.models import model_to_dict
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from common.classviews import ModelView, TemplateView, FormView, CreateView, UpdateView, DetailView, ListView
from . import forms, models
from . import appname
from .zkz import zkz_dict
from pay.models import order
from pay import get_pay_url

ConstantContext = {'now':datetime.now,}
ADMIN_KEY = (
    ('管理', 'admin',),
    ('查看报名情况','stat',),
    ('配置', 'config',),

)
ORDI_KEY = (
    ('报名', 'submit',),
    ('缴费', 'pay',),
    ('打印报名表','detail',),
    ('打印准考证','zkz',),
    ('查询成绩','query',),
)
ADMIN_MENU = tuple((name, code+'_menu') for name, code in ADMIN_KEY)
ORDI_MENU = tuple((name, code+'_menu') for name, code in ORDI_KEY)
VIEW_DICT = dict(ADMIN_KEY+ORDI_KEY)
ORDINARY_MENUS = tuple(e for e, f in ORDI_MENU)
ConstantContext.update(settings.XIAN_CONTEXT[appname])
ConstantContext.update({'ADMIN_MENU':ADMIN_MENU,'ORDI_MENU' :ORDI_MENU})

def mapping2query(mapping):
    return '&'.join('%s=%s'%(k,v) for k, v in mapping.items())

def query2mapping(query):
    return dict(e.split('=') for e in query.split('&'))

class ConfigViewMixin(object):

    config = None
    appname = __file__.replace('\\','/').rsplit('/',2)[1]

    def _get_configs(self):
        if not hasattr(self, '_configs'):
            self._configs = models.Config.memory_refresh()
        return self._configs
    
    configs = property(_get_configs)

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('config_pk') 
        if pk is not None:
            try:
                self.config = self.configs[pk]
                # 普通视图要进行可用性判断
                if self.menu in ORDINARY_MENUS and not self.config.enable:
                    return self.error_response('当前考试不可用.') 
                self.model = self.config.model
                self.form_class = self.config.form_class
            except (KeyError, AttributeError) as e:
                return self.error_response('找不到对应的考试') 
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'configs':self.configs,'config' :self.config})
        context.update(ConstantContext)
        return context

    def error_response(self, message, **kwargs):
        if self.config is not None:
            message = self.config.title + '\n' + message
        return super().error_response(message, **kwargs)

class blank_zkz(ConfigViewMixin, TemplateView):
    # 暂时没做
    template_name = appname+'/blank_zkz.html'
    
    # def get(self, request, *args, **kwargs):
    #     pass

class create(ConfigViewMixin, CreateView):

    template_name = appname+'/form.html'

    def post(self, request, *args, **kwargs):
        return self._dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._dispatch(request, *args, **kwargs)

    def _dispatch(self, request, *args, **kwargs):
        t0, t1 = self.config.submit0, self.config.submit1
        if not (t0 < datetime.now() < t1):
            return self.error_response(
                '不在报名的时间范围内\n开始:%(start)s\n结束:%(end)s',
                start=t0.strftime('%Y-%m-%d %H:%M:%S'),
                end=t1.strftime('%Y-%m-%d %H:%M:%S'))
        has_history = self.model.objects.filter(creater=request.user)
        if has_history:
            latest = has_history.last()
            if latest.config==self.config.id:
                return self.error_response("不能重复报名")
            else:
                self.latest = latest
        return getattr(super(), request.method.lower())(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['config']=self.config
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if hasattr(self, 'latest'):
            # 读取最近一次历史记录作为初始值
            hisdic = model_to_dict(self.latest)
            # 头像、报考岗位和联系电话不读取历史记录
            hisdic.pop('bkgw')
            hisdic.pop('lxdh')
            hisdic.pop('tx')
            initial.update(hisdic)
        return initial 

    def form_valid(self, form):
        self.object = form.save(commit = False)
        self.object.creater = self.request.user
        self.object.config = self.config.id
        self.object.save()
        if self.request.is_ajax():
            data = {'valid':True, 'url':self.get_success_url()}
            return JsonResponse(data)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.rvs('submit',**self.config.kwargs)

class update(ConfigViewMixin, UpdateView):

    template_name = appname+'/form.html'

    def post(self, request, *args, **kwargs):
        return self._dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._dispatch(request, *args, **kwargs)

    def _dispatch(self, request, *args, **kwargs):
        t0, t1 = self.config.submit0, self.config.submit1
        if not (t0 < datetime.now() < t1):
            return self.error_response(
                '不在报名的时间范围内\n开始:%(start)s\n结束:%(end)s',
                start=t0.strftime('%Y-%m-%d %H:%M:%S'),
                end=t1.strftime('%Y-%m-%d %H:%M:%S'))
        self.object = self.get_object()
        if self.object.check_status==1:
            return self.error_response("报名信息已通过审核,无法修改")
        if self.object.check_status==0:
            return self.error_response("报名信息审核中,无法修改")
        return getattr(super(), request.method.lower())(request, *args, **kwargs)

    def get_lookup_dict(self):
        return {
            'creater' : self.request.user,
            'config': self.config.id,
        }

    def get_success_url(self):
        return self.rvs('submit',**self.config.kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['config']=self.config
        return kwargs

    def form_valid(self, form):
        if not form.cleaned_data['tx']:
            form.cleaned_data.pop('tx')
        self.object = form.save(commit = False)
        self.object.check_status = 0
        self.object.save()
        if self.request.is_ajax():
            data = {'valid':True, 'url':self.get_success_url()}
            return JsonResponse(data)
        return HttpResponseRedirect(self.get_success_url())

class admin_detail(ConfigViewMixin, DetailView):

    def get_template_names(self):
        return ['%s/%s/admin_detail.html'%(appname,self.config.model_name)]

    def get_object(self):
        obj = super().get_object()
        for k, v in obj.__dict__.items():
            if v is None:
                setattr(obj, k, '')
        return obj

class index(ConfigViewMixin, ListView):

    def get_queryset(self):
        query_dict={'config':self.config.id}
        query_dict.update(self.request.GET.dict())
        return self.model.objects.filter(**query_dict).select_related('creater')

    def get_template_names(self):
        return ['%s/%s/index.html'%(appname, self.config.model_name)]


class config_create(ConfigViewMixin, CreateView):

    form_class = forms.ConfigForm
    model = models.Config
    template_name = appname+'/config_form.html'

    def get_initial(self):
        initial = super().get_initial()
        now = datetime.now()
        start = now.replace(hour=9,minute=0,second=0)# + timedelta(1)
        end = now.replace(hour=17,minute=0,second=0) + timedelta(4)
        for k, v in self.form_class.base_fields.items():
            if k[-1] == '0':
                initial[k]=start
            elif k[-1] == '1':
                initial[k]=end
        return initial 

    def get_success_url(self):
        return self.rvs('config_menu')

class config_update(ConfigViewMixin, UpdateView):

    form_class = forms.ConfigForm
    model = models.Config
    template_name = appname+'/config_form.html'

    def get_success_url(self):
        return self.rvs('config_menu')

    def get_initial(self):
        initial = super().get_initial()
        return initial 

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        alert = localtime(self.object.zkz0).replace(tzinfo=None)
        if settings.DEBUG is False and alert < datetime.now() and request.user.sfzh!='000000000000000000':
            return self.error_response('准考证打印环节已开始, 无法修改考试配置信息')
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

class config_menu(ConfigViewMixin, ListView):
    model = models.Config
    template_name = appname+'/config_menu.html'

    def get_queryset(self):
        return self.model.objects.all().order_by('-id')

class config_detail(ConfigViewMixin, DetailView):

    model = models.Config
    template_name = appname+'/config_detail.html'

    def get_object(self):
        obj = super().get_object()
        for k, v in obj.__dict__.items():
            if isinstance(v, datetime):
                setattr(obj, k, localtime(v).replace(tzinfo=None))
        return obj

class submit(ConfigViewMixin, TemplateView):

    template_name = appname+'/submit.html'

    def get(self, request, *args, **kwargs):
        config = self.config
        model = config.model
        user = self.request.user
        now = datetime.now()
        action = ''
        action_url = ''
        message = config.title
        message_color = 'black'
        si0 = getattr(config, 'submit0', None) or config.min_date
        si1 = getattr(config, 'submit1', None) or config.max_date
        if not (si0 < now <si1):
            message='不在报名时间范围内'
        else:
            result = model.objects.filter(creater=user, config=config.id)
            try:
                record = result.get()
                if record.check_status == 1:
                    message = '已通过审核'
                    message_color = 'green'
                    action='查看报名信息'
                    action_url=self.rvs('detail',**config.kwargs)
                elif record.check_status == 0:
                    message = '待审核'
                else:
                    message = '未通过审核, %s'%record.message
                    message_color = 'red'
                    action = '编辑'
                    action_url=self.rvs('update',**config.kwargs)
            except model.DoesNotExist as e:
                return HttpResponseRedirect(self.rvs('create',**config.kwargs))
                # action='报名'
                # action_url=self.rvs('create',**config.kwargs)
        context = self.get_context_data(
            action=action, action_url=action_url, 
            message=message, message_color=message_color,
        )
        return self.render_to_response(context)

class menu(ConfigViewMixin, TemplateView):

    action = ''
    template_name = appname+'/menu.html'

    def get(self, request, *args, **kwargs):
        menu_objs = []
        user = self.request.user
        for key, config in reversed(tuple(self.configs.items())):
            if self.menu in ORDINARY_MENUS and not config.enable:
                continue
            menu_objs.append({
                'title':config.title, 
                'title_url':config.url,
                'action': self.action or self.menu, 
                'action_url':self.get_action_url(config),
            })
        context = self.get_context_data(menu_objs=menu_objs)
        return self.render_to_response(context)

    def get_action_url(self, config):
        return self.rvs(VIEW_DICT[self.menu], **config.kwargs)+"?user="+str(self.request.user.pk)

class submit_menu(menu):
    action = '进入'

class pay_menu(menu):
    pass

class detail_menu(menu):
    pass

class zkz_menu(menu):
    pass

class query_menu(menu):
    pass

class stat_menu(menu):
    template_name = appname+'/admin_menu.html'

class admin_menu(menu):
    template_name = appname+'/admin_menu.html'

    def get_action_url(self,config):
        return self.rvs(VIEW_DICT[self.menu], query_type='check_pending', **config.kwargs)

class pay(ConfigViewMixin, DetailView):

    template_name = appname+'/pay.html'

    def get_lookup_dict(self):
        return {
            'creater' : self.request.user,
            'config'  : self.config.id,
        }

    def get(self, request, *args, **kwargs):
        config = self.config
        if not config.fee:
            return self.error_response("此次考试无需缴费")
        t0, t1 = self.config.pay0, self.config.pay1
        if not (t0 < datetime.now() < t1):
            return self.error_response(
                '不在缴费的时间范围内\n开始:%(start)s\n结束:%(end)s',
                start=t0.strftime('%Y-%m-%d %H:%M:%S'),
                end=t1.strftime('%Y-%m-%d %H:%M:%S'))
        try:
            self.object = self.get_object()
        except Http404 as e:
            return self.error_response('没有报名记录,无法缴费')
        if self.object.check_status != 1:
            return self.error_response("只有通过审核的考生才能缴费")   
        action = ''
        action_url = ''
        message = config.title
        message_color = 'black'
        if self.object.is_pay == True:
            context = self.get_context_data(action=action, action_url=action_url, 
                message='您已缴费,请及时打印报名表和准考证', message_color='green')
            return self.render_to_response(context)
        # 在缴费时间范围内,通过审核,没有缴费的考生, 引导到支付宝支付页面
        obj = self.object
        base_dict = dict(
            app=obj._meta.app_label, model_name=obj._meta.model_name, 
            object_id=obj.pk, creater=self.request.user)
        try:
            od = order.objects.get(**base_dict)
        except order.DoesNotExist:
            od = order(out_trade_no=self.get_order_number(),**base_dict)
            od.save()
        alipay_url = get_pay_url(
            out_trade_no=od.out_trade_no, subject=config.title, 
            total_fee=config.fee, body='考试缴费')
        return HttpResponseRedirect(alipay_url)

    def get_order_number(self):
        now=datetime.now()
        return str(now.strftime("%Y%m%d%H%M%S"))+str(now.microsecond)

class GuardMixin(object):

    '根据config，object和time进行一系列拦截验证'

    action = '进行此操作'

    def get_lookup_dict(self):
        return {
            'creater' : self.request.user,
            'config'  : self.config.id,
        }

    def dispatch(self, request, *args, **kwargs):
        result = self.time_check_passed()
        if result is not None:
            return result
        try:
            self.object = self.get_object()
        except Http404 as e:
            return self.error_response('没有报名记录,无法%s'%self.action)
        if self.object.check_status != 1:
            return self.error_response("只有通过审核的考生才能%s"%self.action)   
        if self.config.fee and self.object.is_pay != True:
            return self.error_response("您还没缴费, 无法%s"%self.action) 
        return super().dispatch(request, *args, **kwargs)

    def time_check_passed(self):
        name = self.__class__.__name__
        t0, t1 = getattr(self.config, name+'0'), getattr(self.config, name+'1')
        if not (t0 < datetime.now() < t1):
            return self.error_response(
                '不在%(action)s的时间范围内\n开始:%(start)s\n结束:%(end)s',
                action=self.action,
                start =t0.strftime('%Y-%m-%d %H:%M:%S'),
                end   =t1.strftime('%Y-%m-%d %H:%M:%S'))

class detail(ConfigViewMixin, GuardMixin, TemplateView):

    action = '打印报名表'

    def get_object(self):
        obj = super().get_object()
        for k, v in obj.__dict__.items():
            if v is None:
                setattr(obj, k, '')
        return obj

    def get_template_names(self):
        return ['%s/%s/detail.html'%(appname,self.config.model_name)]


class zkz(ConfigViewMixin, GuardMixin, TemplateView):

    template_name= appname+'/zkz.html'
    action = '打印准考证'

    def get_context_data(self, **kwargs):
        user=self.request.user
        context=super().get_context_data(**kwargs)
        context['zkz_config']=zkz_dict[self.object.bkgw]
        tn=['考生需要在早上7点40之前到达考场参加体能测试，早上8点钟封考场后不得进入考场。']
        qt=["考生应带好有效居民身份证和准考证及其他考试用品。", 
            "考生应在考试当日早上8:30之前到达考室。", 
            "考试当日9:30之后考生不得再进入考试参加考试。"]
        if context['zkz_config']['kskm']=='体能测试':
            context['special_rules']=tn
        else:
            context['special_rules']=qt
        return context

class query(ConfigViewMixin, GuardMixin, TemplateView):

    template_name= appname+'/query.html'
    action = '查询成绩'

    def time_check_passed(self):
        config = self.config
        t0, t1 = config.bscj0, config.bscj1
        a0, a1 = config.all0, config.all1
        now = datetime.now()
        if not (t0 < now < t1) and not (a0 < now < a1):
            return self.error_response('不在查询成绩的时间范围内')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_query_all'] = self.config.all0 < datetime.now() < self.config.all1
        return context

class admin_zkz(ConfigViewMixin, DetailView):

    template_name= appname+'/zkz.html'

    def get_context_data(self, **kwargs):
        user=self.request.user
        context=super().get_context_data(**kwargs)
        context['zkz_config']=zkz_dict[self.object.bkgw]
        tn=['考生需要在早上7点40之前到达考场参加体能测试，早上8点钟封考场后不得进入考场。']
        qt=["考生应带好有效居民身份证和准考证及其他考试用品。", 
            "考生应在考试当日早上8:30之前到达考室。", 
            "考试当日9:30之后考生不得再进入考试参加考试。"]
        if context['zkz_config']['kskm']=='体能测试':
            context['special_rules']=tn
        else:
            context['special_rules']=qt
        return context

class stat(ConfigViewMixin, TemplateView):
    template_name = appname+'/stat.html'

    def get(self, request, *args, **kwargs):
        stat_list = []
        for name, num in self.config.bkgw.items():
            e = [name, num]
            for status in (0, 1, -1):
                qd = dict(bkgw=name, check_status=status)
                e.append(len(self.model.objects.filter(config=self.config.id, **qd)))
                e.append(self.rvs('index', **self.config.kwargs)+'?'+mapping2query(qd))
            stat_list.append(e)
        context = self.get_context_data(stat_list=stat_list)
        return self.render_to_response(context)

class check_all_alive_zkz(ConfigViewMixin, TemplateView):

    template_name=appname+'/check_all_alive_zkz.html'

    def get_queryset(self):
        return models.hetong.objects.filter(config__in=[9,10,11],check_status=1).order_by('zkzh')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        object_list = []
        for e in queryset:
            zkzd=zkz_dict[e.bkgw]
            e.__dict__.update(zkzd)
            object_list.append(e)
        context = self.get_context_data(
            object_list     = object_list,
        )
        return self.render_to_response(context)

class admin(ConfigViewMixin, ListView):
    "用于审核及录入成绩的表格化管理视图,post方法仅支持ajax"
    #template_name = appname+'/admin.html'

    menu_dict = {
        True:OrderedDict((
            ('check_pending',          ({'check_status':0}, ('bkgw',))),
            ('check_not_pay',        ({'check_status':1,'is_pay':False}, ('bkgw',))), # 通过审核但未缴费
            ('check_passed',        ({'check_status':1,'is_pay':True}, ('bkgw',))),
            ('check_refused',      ({'check_status':-1}, ('bkgw',))),
            ('bscj_todo', ({'check_status':1,'is_pay':True,'bscj':-1}, ('zkzh',))),
            ('bscj_done', ({'check_status':1,'is_pay':True,'bscj__gt':-1}, ('bkgw','-bscj'))),
            ('mscj_todo', ({'check_status':1,'is_pay':True,'is_mianshi':True,'mscj':-1}, ('bkgw','-bscj'))),
            ('mscj_done', ({'check_status':1,'is_pay':True,'is_mianshi':True,'mscj__gt':-1},('bkgw','-zcj'))),
            ('final_list',({'check_status':1,'is_pay':True,'is_tijian':True,}, ('bkgw','-zcj'))),
        )),
        False:OrderedDict((
            ('check_pending',          ({'check_status':0}, ('bkgw',))),
            ('check_not_pay',        ({'check_status':1}, ('bkgw',))), 
            ('check_passed',        ({'check_status':1}, ('bkgw',))),
            ('check_refused',      ({'check_status':-1}, ('bkgw',))),
            ('bscj_todo', ({'check_status':1,'bscj':-1}, ('zkzh',))),
            ('bscj_done', ({'check_status':1,'bscj__gt':-1}, ('bkgw','-bscj'))),
            ('mscj_todo', ({'check_status':1,'is_mianshi':True,'mscj':-1}, ('bkgw','-bscj'))),
            ('mscj_done', ({'check_status':1,'is_mianshi':True,'mscj__gt':-1},('bkgw','-zcj'))),
            ('final_list',({'check_status':1,'is_tijian':True,}, ('bkgw','-zcj'))),
        )),
    }

    _menu_cn = {
        True:OrderedDict((
            ('check_pending', '待审核'),
            ('check_not_pay', '通过审核未缴费'),
            ('check_passed', '通过审核已缴费'),
            ('check_refused','未通过审核'),
            ('bscj_todo','待录入-笔试成绩'),
            ('bscj_done', '已录入-笔试成绩'),
            ('mscj_todo','待录入-面试成绩'),
            ('mscj_done', '已录入-面试成绩'),
            ('final_list','体检名单'),
        )),
        False:OrderedDict((
            ('check_pending', '待审核'),
            ('check_passed', '通过审核'),
            ('check_refused','未通过审核'),
            ('bscj_todo','待录入-笔试成绩'),
            ('bscj_done', '已录入-笔试成绩'),
            ('mscj_todo','待录入-面试成绩'),
            ('mscj_done', '已录入-面试成绩'),
            ('final_list','体检名单'),
        )),
    }

    def get(self, request, *args, **kwargs):
        self.query_type = kwargs.get('query_type', 'check_pending')
        flag = bool(int(self.config.fee))
        self.query, self.order = self.menu_dict[flag][self.query_type]
        self.menu_cn = self._menu_cn[flag]
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        "和前端js函数密切联系.目前是button.js的get_post_data"
        if not request.is_ajax():
            return self.error_response('') #'仅支持AJAX提交请求'
        name = request.POST.get('name')
        pk = request.POST.get('pk')
        value = request.POST.get('value') 
        errors = self.model.validate_field(name, value)
        if not errors:
            self.model.save_field(pk, name, value)
            return JsonResponse({'valid':True})
        else:
            return JsonResponse({'valid':False, 'errors':errors})

    def get_queryset(self):
        self.query['config'] = self.config.id
        return self.model.objects.filter(**self.query).order_by(*self.order)

    def get_template_names(self):
        return ['%s/%s/admin.html'%(appname,self.config.model_name)]

    # def get_context_data(self, **kwargs):
    #     "admin.html的check_status渲染要用到"
    #     from django.forms import RadioSelect
    #     return super().get_context_data(radio=RadioSelect, **kwargs)

class write(ConfigViewMixin, ModelView):

    query_type=''

    def get_redirect_url(self):
        return self.rvs('admin', query_type=self.query_type, **self.config.kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.get_redirect_url())

class write_zkzh(write):

    query_type='bscj_todo'

    def get(self, request, *args, **kwargs):
        config = self.config
        now = datetime.now()
        if settings.DEBUG is False and config.zkz0 < now:
            return self.error_response('准考证打印环节已开始, 无法设置准考证号')
        if config.submit1 > now:
            return self.error_response('报名时间还没结束, 无法设置准考证号')
        self.model.write_zkzh(self.config)
        return super().get(self, request, *args, **kwargs)

class write_bspm(write):

    query_type='bscj_done'

    def get(self, request, *args, **kwargs):
        self.model.write_bspm_and_is_mianshi(self.config)
        return super().get(self, request, *args, **kwargs)

class write_zpm(write):

    query_type='mscj_done'

    def get(self, request, *args, **kwargs):
        self.model.write_zpm_and_is_tijian(self.config)
        return super().get(self, request, *args, **kwargs)

class download(ConfigViewMixin, ModelView):

    xxx = {
        'bspm':(
            ['zkzh','xm','bkgw',] + ['bscj', 'bspm'],
            'is_mianshi',
            {'bscj__gt':-1},
            '笔试成绩及排名',
            ('bkgw','-bscj'),
        ),
        'zpm' :(
            ['zkzh','xm','bkgw',] + ['bscj','mscj', 'zcj', 'zpm'],
            'is_tijian',
            {'mscj__gt':-1},
            '总成绩及排名',
            ('bkgw','-zcj'),
        ),
        'zkzh' :(
            ['creater','xm','bkgw','zkzh'] ,
            'is_tijian',
            {},
            '准考证名单',
            ('zkzh',),
        ),
    }
    
    def get(self, request, *args, **kwargs):
        # excel文件名不能为中文
        COL_UNIT_WIDTH = 300
        row_height = xlwt.easyxf('font:height 320;')
        style = xlwt.easyxf('border: top thin, right thin, bottom thin, left thin;')
        style_gray = xlwt.easyxf('pattern: pattern solid, fore_colour gray25;border: top thin, right thin, bottom thin, left thin;')

        field = self.kwargs['field']
        try:
            columns, tag_field, cj_field, sheet_name, order = self.xxx[field]
        except KeyError as e:
            return self.error_response('无效下载字段:'+field)
        xls_name = '%s_%s.xls' % (self.config.id, field)
        self.wb = xlwt.Workbook() 
        self.sht = self.wb.add_sheet('%s_%s'%(self.config.id,sheet_name))

        obj_index = [[0]+[self.model._meta.get_field(code).verbose_name for code in columns]]
        obj_index.extend([[getattr(obj, tag_field)] + [getattr(obj, name) for name in columns] 
                for obj in self.model.objects.filter(config=self.config.id,
                    check_status=1,**cj_field).order_by(*order)])        
        max_len = {}
        for row, obj in enumerate(obj_index):
            cell_style = style_gray if obj[0] else style
            for col, value in enumerate(obj[1:]):
                value = str(value)
                if col not in max_len:
                    max_len[col] = 0
                try:
                    float(value)
                    rate = 1
                except ValueError as e:
                    rate = 2
                max_len[col] = max(max_len[col], len(value)*rate)
                self.sht.write(row, col, value, cell_style)
            self.sht.row(row).set_style(row_height)
        for col, length in max_len.items():
            self.sht.col(col).width = COL_UNIT_WIDTH*length

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="%s"'%xls_name
        self.wb.save(response)
        return response
