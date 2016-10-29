import re
import os
from itertools import cycle
from datetime import date, datetime
from collections import OrderedDict

from django.utils.safestring import mark_safe
from django.forms.models import model_to_dict
from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core import validators
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.utils.timezone import localtime

from . import appname

User = settings.AUTH_USER_MODEL

CHOICE_KAOSHI = (
    ('hetong', '劳动合同制'), 
)
CHOICE_XB = (('男','男'),('女','女'))
CHOICE_HF = (('是','是'),('否','否'),)
CHOICE_HYZK = (
    ('未婚','未婚'),
    ('已婚','已婚'),
    ('离异','离异'),
    ('丧偶','丧偶'),
)
CHOICE_KSSF=(
    ('公务员','公务员'),
    ('参公人员','参公人员'),
    ('事业编制人员','事业编制人员'),
    ('应届毕业生','应届毕业生'),
    ('待业','待业'),
    ('其他','其他'),
)
CHOICE_KSLX = (
    ('应届毕业生','应届毕业生'), 
    ('往届毕业生','往届毕业生'),
)
CHOICE_XXLB = (
    ('全日制','全日制'), 
    ('在职','在职'),
)
CHOICE_ZZMM=(
    ("群众","群众"),
    ("中共党员","中共党员"),
    ("中共预备党员","中共预备党员"),
    ("共青团员","共青团员"),
    ("无党派民主人士","无党派民主人士"),
    ("民革党员","民革党员"),
    ("民盟盟员","民盟盟员"),
    ("民建会员","民建会员"),
    ("民进会员","民进会员"),
    ("农工党党员","农工党党员"),
    ("致公党党员","致公党党员"),
    ("九三学社社员","九三学社社员"),
    ("台盟盟员","台盟盟员"),
)
CHOICE_STZK=(
    ('好','好'),
    ('良好','良好'),
    ('一般','一般'),
    ('差','差'),
)
CHOICE_XL=(('',''),
    ('大专','大专'),
    ('中专','中专'),
    ('中技','中技'),
    ('本科','本科'),
    ('硕研','硕士研究生'),
    ('博研','博士研究生'),
    ('高中','高中'),
    ('初中','初中'),
    ('其他','其他'),
)
CHOICE_XW=(
    ('',''),
    ('学士','学士'),
    ('硕士','硕士'),
    ('博士','博士'),
)

@deconstructible
class ArrayValidator(object):
    """
    验证用户提交合法的二维数据, 如果通过验证,则返回一个数组
    """
    def __init__(self, regexs=None, row_dlt='\n',col_dlt=','):
        self.row_dlt = row_dlt
        self.col_dlt = col_dlt
        if regexs is None:
            self.regexs = [re.compile('.*')]
        else:
            for i, regex in enumerate(regexs):
                if isinstance(regex, str):
                    regexs[i] = re.compile(regex)    
            self.regexs = regexs       
        self.col_num = len(self.regexs)

    def __call__(self, value):
        rd = self.row_dlt
        cd = self.col_dlt
        cn = self.col_num
        value = value.strip().replace('\r\n','\n').replace('\t',',')
        if cd == ',':
            value = value.replace('，', cd)
            cd_han = '逗号'
        else:
            cd_han = '","'
        res = []
        for i, row in enumerate(value.split(rd)):
            record = row.split(cd)
            rn = len(record)
            if rn != cn:
                raise ValidationError('每行应有%s个元素(第%s行目前是%s个)'%(cn,i+1, rn))
            for j, ele in enumerate(zip(record, self.regexs)):
                word, regex = ele
                word = word.strip()
                if not regex.match(word):
                    raise ValidationError('第%s行第%s个元素(%s)格式不符合要求'%(i+1, j+1, word))
                record[j] = word
            if rn == 1:
                record=record[0]
            res.append(record)
        return res

class ConfigNormalizeHolder(object):

    enable = False
    min_date = datetime(3000,1,1)
    max_date = datetime(3000,1,1)

    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.title)

    @property
    def kwargs(self):
        return {'config_pk':self.id}

class InMemoryMixin(object):

    memory = OrderedDict()
    array_fields = 'bkgw','bbsgw','bsmenu','special_rules'

    @staticmethod
    def is_array_validator(ins):
        return isinstance(ins, ArrayValidator)

    @classmethod
    def memory_size(cls):
        from sys import getsizeof as gz
        total = 0
        for config in cls.memory.values():
            total += sum(gz(e) for e in config.__dict__.values())
        return round(total/1024, 1)

    @classmethod
    def memory_clear(cls):
        cls.memory.clear()

    @classmethod
    def memory_refresh(cls):
        for self in cls.objects.all():
            self.memory_update()
        return cls.memory

    def memory_update(self):
        self.memory[str(self.pk)] = self.normalize_to_config()

    def normalize_to_config(self):
        "把ins转换为一个config实例"
        from . import forms
        from . import models
        init_dict = model_to_dict(self.normalize())
        init_dict.update(settings.XIAN_CONTEXT[appname])
        config = ConfigNormalizeHolder(**init_dict)
        name = self.model_name
        config.model = getattr(models, name)
        config.form_class = getattr(forms, name)
        return config

    def normalize(self):
        self.normalize_time_fields()
        self.normalize_array_fields()
        self.normalize_special_fields()
        return self

    def normalize_time_fields(self):
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                setattr(self, k, localtime(v).replace(tzinfo=None))
        return self

    def normalize_array_fields(self):
        "require self define array_fields"
        for k, v in self.__dict__.items():
            if k in self.array_fields:
                if not v:
                    setattr(self, k, [])
                else:
                    field = self._meta.get_field(k)
                    validator = None
                    for validator in field.validators:
                        if self.is_array_validator(validator):
                            break
                    if validator is None:
                        raise ImproperlyConfigured('cannot normalize field: %s'%k)
                    new_v = validator(v)
                    if new_v is None:
                        raise ImproperlyConfigured('normalize field %s to None'%k)
                    setattr(self, k, new_v)
        return self

    def normalize_special_fields(self):
        self.bkgw = OrderedDict(self.bkgw)
        return self

    def save(self):
        super().save()
        self.memory_update()
        return self

class Config(InMemoryMixin, models.Model):

    #InMemoryMixin必须放到models.Model之前, 否则其save方法调用不到

    class Meta:
        verbose_name = "考试配置"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.title)

    # 系统字段
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name='编辑时间',auto_now=True)

    enable = models.BooleanField(verbose_name='激活', default=False) 
    model_name = models.CharField(verbose_name='报名表类型', max_length=20, choices=CHOICE_KAOSHI, default='') 
    url = models.URLField(verbose_name='公告链接', default='') 
    title = models.CharField(verbose_name='考试标题', max_length=80, default='', unique=True,
        validators=[validators.MinLengthValidator(2)], ) 
    fee = models.PositiveIntegerField(verbose_name='报名费', default=0) 
    jingzheng_rate = models.PositiveSmallIntegerField(verbose_name='录取比例(面试数:录取数)',default=3)
    bscj_rate = models.FloatField(verbose_name='笔试比重',default=0.5)
    mscj_rate = models.FloatField(verbose_name='面试比重',default=0.5)
    bkgw = models.CharField(verbose_name='岗位及其录取数', max_length=500, default='', 
        validators=[ArrayValidator(['\w{2,20}','\d{1,3}'])]) 
    bbsgw = models.CharField(verbose_name='不笔试岗位', max_length=500, default='', blank=True,
        validators=[ArrayValidator(['\w{2,20}'])]) 
    special_rules = models.CharField(verbose_name='特别规定', max_length=500, default='', blank=True,
        validators=[ArrayValidator(col_dlt='\t')]) 
    bsmenu = models.CharField(verbose_name='考试时间地点科目', max_length=500, default='',
        validators=[ArrayValidator(['\w{2,20}','\w{2,20}','\w{2,20}'])]) 
    submit0 = models.DateTimeField(verbose_name='报名开始时间')
    submit1 = models.DateTimeField(verbose_name='报名结束时间')
    pay0 = models.DateTimeField(verbose_name='缴费开始时间')
    pay1 = models.DateTimeField(verbose_name='缴费结束时间')
    detail0 = models.DateTimeField(verbose_name='打印报名表开始时间')
    detail1 = models.DateTimeField(verbose_name='打印报名表结束时间')
    zkz0 = models.DateTimeField(verbose_name='打印准考证开始时间')
    zkz1 = models.DateTimeField(verbose_name='打印准考证结束时间')
    bscj0 = models.DateTimeField(verbose_name='查询笔试成绩开始时间')
    bscj1 = models.DateTimeField(verbose_name='查询笔试成绩结束时间')
    all0 = models.DateTimeField(verbose_name='查询总成绩开始时间')
    all1 = models.DateTimeField(verbose_name='查询总成绩结束时间')

    article = models.TextField(verbose_name='公告',max_length=5000, default='',blank=True)

class BaseKaoshi(models.Model):
    """
    """
    class Meta:
        abstract = True 
        unique_together = 'creater','config'

    # 允许调用save_field方法的字段
    ADMIN_FIELDS = ('check_status','message', 'bscj','mscj')
    # 系统字段
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name='编辑时间',auto_now=True)
    # 管理字段
    creater = models.ForeignKey(User,verbose_name='身份证号',related_name="%(app_label)s_%(class)s_set")
    config = models.IntegerField(verbose_name='配置',default=0)
        #审核
    check_status = models.IntegerField(verbose_name='审核状态', default=0, choices=((-1,'拒绝'),(0,'复原'),(1,'通过')),)
    message = models.TextField(verbose_name='消息',max_length=500, default='',) # validators=[v1,v2]
    is_pay = models.BooleanField(verbose_name='是否缴费',default=False)
        #笔试
    zkzh = models.CharField(verbose_name='准考证号',max_length=50, default='')
    bscj = models.FloatField(verbose_name='笔试成绩',default=-1, validators=[validators.MinValueValidator(-1),validators.MaxValueValidator(100)])
    mscj = models.FloatField(verbose_name='面试成绩', default=-1, validators=[validators.MinValueValidator(-1),validators.MaxValueValidator(100)])
    zcj = models.FloatField(verbose_name='总成绩', default=-1, validators=[validators.MinValueValidator(-1),validators.MaxValueValidator(100)])
    bspm = models.SmallIntegerField(verbose_name='笔试排名',default=0) 
    zpm = models.SmallIntegerField(verbose_name='总排名', default=0)
        #面试
    is_mianshi = models.BooleanField(verbose_name='进入面试',default=False) 
    is_tijian = models.BooleanField(verbose_name='进入体检',default=False)



    def __str__(self):
        return self.xm

    @classmethod
    def save_field(cls, pk, name, value):
        "一次修改一个字段值"
        ins = cls.objects.get(pk=pk)
        setattr(ins, name, value)
        ins.save()
        return ins

    @classmethod
    def validate_field(cls, name, value):
        if name not in cls.ADMIN_FIELDS:
            return
        #"当使用Postgresql数据库时,IntegerField会自动加上max和min两个validator"
        #"这个时候就要求把能够数字化的字符串数字化"
        try:
            value = float(value)
        except ValueError as e:
            pass
        errors = []
        field = cls._meta.get_field(name)
        for validator in field.validators:
            try:
                validator(value)
            except ValidationError as e:
                errors.append(e)
        if errors:
            return {name:ValidationError(errors).messages}

    def render_field(self, name, render_value=True, kwargs=None, attrs=None):
        '''
        通过model实例渲染其某个字段的hmtl表单代码的方法, 其中
        0) 如果这个字段有特殊渲染法, 则调取特殊渲染
        1) kwargs是传给form field的参数, 类似于forms.CharField(**kwargs)
        2) attrs是传给widget的参数, 例如定义attrs={'class':'blur','style':"margin:auto"}
        '''
        special_method = 'render_' + name
        if hasattr(self, special_method):
            return getattr(self, special_method)(name, render_value, kwargs, attrs)
        if kwargs is None:
            kwargs = {}
        if attrs is None:
            attrs = {}
        if render_value:
            value = getattr(self, name)
        else:
            value = None
        return self._meta.get_field(name).formfield(**kwargs).widget.render(
            value=value, name=name, attrs=attrs)   

    def render_check_status(self, name, render_value=True, kwargs=None, attrs=None):
        from django.utils.safestring import mark_safe
        if attrs is None:
            attrs = {}
        pk = str(self.pk)
        attrs.update({'type':'radio'})
        id_str = "id-%s-%s" % (name, pk)
        elements = []
        for i, ele in enumerate(self._meta.get_field(name).choices):
            value, read_value = ele
            dynamic={'value':value,'id':'%s-%s'%(id_str,i), 'name':name+'-'+pk}
            if render_value and getattr(self, name) == value:
                dynamic['checked']='checked'
            dynamic.update(attrs)
            attr_str=' '.join('%s="%s"'%(k,v)for k, v in dynamic.items())
            input = '<input %s />' % attr_str
            elements.append('<li><label for="%(id_str)s-%(i)s">%(input)s%(read_value)s</label></li>'%locals())
        elements = '\n'.join(elements)
        return mark_safe('<ul id="%(id_str)s">\n%(elements)s\n</ul>'%locals())

    @property
    def age(self):
        try:
            sfz = self.creater.sfzh
            age = datetime.now() - datetime(int(sfz[6:10]),int(sfz[10:12]),int(sfz[12:14]))
            age = age.days // 365
        except Exception as e:
            age = 0
        return age

    @property
    def readable_lxdh(self):
        s = self.lxdh
        return '%s %s %s'%(s[:3],s[3:7],s[7:])

    @property
    def csny(self):
        s = self.creater.sfzh
        return s[6:10]+'-'+s[10:12]

    def get_absolute_url(self):
        return reverse('%s:%s_detail'%(self._meta.app_label, self._meta.model_name),kwargs={'config_pk':self.config})

    @classmethod
    def group_by_count(cls, field_str, qset=None):
        "暂时用不到这个方法."
        if qset is None:
            qset = cls.objects.all()
        # 试验证明qset不能包含双重排序,例如order_by(field1,field2),否则 field_order会返回重复数据
        # 当然, 给本方法传一个包含order_by的qset是没有什么意义的.所以主要责任在调用者.
        # 解决办法有一: 最后再加个order_by(). 
        # 详见:http://stackoverflow.com/questions/327807/django-equivalent-for-count-and-group-by
        field_order=qset.values(field_str).annotate(number=models.Count(field_str))
        for ele in sorted(field_order, key=lambda e:e['number'], reverse=True):
            field = ele[field_str]
            for e in qset.filter(**{field_str:field}):
                yield e

    @classmethod
    def write_zkzh(cls, config):
        "生成准考证号,按 考试种类+年份+次数+考室号+座号"
        passed_dict = {'config':config.id,'check_status':1}
        if config.fee:
            passed_dict['is_pay']=True
        head = str(config.id) + str(cls.category)
        qset = cls.objects.all()
        for gw in config.bbsgw:
            qset = qset.exclude(bkgw=gw)
        num, room = 1, 1
        for e in qset.filter(**passed_dict).order_by('bkgw'):
            e.zkzh = head + str(room).zfill(2) + str(num).zfill(2)
            e.save()
            num += 1
            if num == 31:
                num = 1
                room += 1

    @classmethod
    def write_bspm_and_is_mianshi(cls, config):
        "按岗分组根据笔试成绩生成笔试排名, 可正确处理并列情况,例如1134557"
        "根据竞争比例标记出进入面试的人员"
        passed_dict = {'config':config.id,'check_status':1}
        qset = cls.objects.filter(**passed_dict).order_by('bkgw','-bscj')
        cls._write_pm_and_tag_kaosheng(qset, 'bscj','bspm', 'is_mianshi', config.jingzheng_rate, config)

    @classmethod
    def write_zpm_and_is_tijian(cls, config):
        "根据总成绩生成总排名, 标记进入体检人员名单"
        cls.write_zcj(config)
        passed_dict = {'config':config.id,'check_status':1,'is_mianshi':True}
        qset = cls.objects.filter(**passed_dict).order_by('bkgw','-zcj')
        cls._write_pm_and_tag_kaosheng(qset, 'zcj','zpm', 'is_tijian', 1, config)
 
    @classmethod
    def  _write_pm_and_tag_kaosheng(cls, qset, cj_str, rank_str, tag_str, rate, config):
        '''
        写入排名和标记字段.
        遍历 (岗位, 成员集合), 按成绩字段cj_str倒序排序, 
        通过竞争比例rate和招录数config.bkgw[k]取前n名考生,最后一名允许并列.
        res传过来的集合是按bkgw和cj_str排序的.
            姓名,职位,分数, 排名, 标记
            张五,程序员,78
            李六,程序员,67
            张八,程序员,67
            张三,工程师,80
            李四,工程师,78
            赵三,经理,  77
        排序之后应为:
            姓名,职位,分数,排名, 标记
            张五,程序员,78,1,True
            李六,程序员,67,2,False
            张八,程序员,67,2,False
            张三,工程师,80,1,True
            李四,工程师,78,2,False
            赵三,经理,  77,1,True
        '''
        last_bkgw, last_score, last_rank, nth, cut_num = None,None,None,None,None
        for obj in qset:
            if obj.bkgw == last_bkgw:
                this_score = getattr(obj, cj_str)
                nth += 1
                if this_score != last_score:
                    last_rank = nth
                    last_score = this_score
                    if nth > cut_num:
                        last_tag = False
                setattr(obj, tag_str, last_tag)
                setattr(obj, rank_str, last_rank)
            else:
                setattr(obj, rank_str, 1)
                setattr(obj, tag_str,  True)
                last_bkgw = obj.bkgw
                last_score = getattr(obj, cj_str)
                last_rank = 1 
                last_tag = True
                nth = 1
                cut_num = rate * int(config.bkgw[last_bkgw])
            # print(obj.id,last_bkgw, last_score, last_rank, nth, cut_num)
            obj.save()

    @classmethod
    def write_zcj(cls, config):
        "根据笔试成绩和面试成绩生成总成绩"
        for obj in cls.objects.filter(**{
            'config':config.id,'check_status':1,'is_mianshi':True}):
            obj.zcj = round(
                obj.bscj * config.bscj_rate + 
                obj.mscj * config.mscj_rate, 2)
            obj.save()

class hetong(BaseKaoshi):
    """
    """
    category = 1 # 用于渲染准考证号

    class Meta:
        verbose_name = "劳动合同"
        verbose_name_plural = verbose_name

    # 考生填写字段
    tx = models.ImageField("头像",blank=True, null=True,upload_to=appname+'/avatar') 
    xm   = models.CharField(verbose_name='姓名', max_length=10, default='', validators=[validators.MinLengthValidator(2),])
    xb   = models.CharField(verbose_name='性别', max_length=1, default='',choices=CHOICE_XB) 
    hjszd = models.CharField(verbose_name='户籍所在地',max_length=50,default='',blank=True) 
    kssf = models.CharField(verbose_name='考生身份', max_length=10, default='',choices=CHOICE_KSSF) 
    hf    = models.CharField(verbose_name='婚否',max_length=1,default='',choices=CHOICE_HF) 
    lxdh = models.CharField(verbose_name='联系电话',max_length=20,default='',
        validators=[validators.RegexValidator(regex=r'^\d{7,11}$',message='请填写7到11位纯数字')]) 
    bkgw = models.CharField(verbose_name='报考岗位',max_length=50,default='')
    mz   = models.CharField('民族', max_length=5, default='汉') 
    zzmm = models.CharField(verbose_name='政治面貌', max_length=7, default='',choices=CHOICE_ZZMM)
    xl = models.CharField('学历',max_length=4, default='', choices=CHOICE_XL)
    xw = models.CharField('学位',max_length=4, default='', blank=True, choices=CHOICE_XW)
    bysj = models.DateField('毕业时间', null=True)
    byyx = models.CharField('毕业院校',max_length=50, default='')
    zy   = models.CharField('专业',max_length=50, default='')
    stzk = models.CharField('身体状况', max_length=2, default='',choices=CHOICE_STZK,blank=True)
    zc   = models.CharField('专长',max_length=50, default='',blank=True)
    zgzs   = models.CharField('资格证书',max_length=50, default='',blank=True)
    cjgzsj = models.DateField('参加工作时间', blank=True, null=True)
    xgzdwjgw = models.CharField('现工作单位及岗位', max_length=50, blank=True, default='')
    zgsj = models.CharField('资格时间',max_length=60,blank=True, default='')
    jtzz = models.CharField(verbose_name='家庭住址',max_length=100,default='')
    grjl = models.TextField(verbose_name='个人简历',max_length=1000,default='')  
    jcqk = models.TextField(verbose_name='奖惩情况',max_length=1000,blank=True, default='')   
    jtzycyqk = models.TextField('家庭主要成员情况',max_length=500,default='',blank=True)  

# class kaohe(BaseKaoshi):
#     """
#     """
#     category = 2

#     class Meta:
#         verbose_name = "考核招聘"
#         verbose_name_plural = verbose_name

#     # 考生填写字段
#     tx = models.ImageField("头像",blank=True, null=True,upload_to=appname+'/avatar') 
#     xm   = models.CharField(verbose_name='姓名', max_length=10, default='', validators=[validators.MinLengthValidator(2),])
#     xb   = models.CharField(verbose_name='性别', max_length=1, default='',choices=CHOICE_XB) 
#     mz   = models.CharField('民族', max_length=5, default='汉') 
#     jg   = models.CharField('籍贯', max_length=15, default='') 
#     csd   = models.CharField('出生地', max_length=15, default='') 
#     zzmm = models.CharField(verbose_name='政治面貌', max_length=7, default='',choices=CHOICE_ZZMM)
#     xl = models.CharField('学历',max_length=4, default='',blank=True, choices=CHOICE_XL)
#     xw = models.CharField('学位',max_length=4, default='',blank=True, choices=CHOICE_XW)
#     byyx = models.CharField('毕业院校',max_length=50, default='')
#     zy   = models.CharField('专业',max_length=50, blank=True, default='')

#     lxdh = models.CharField(verbose_name='联系电话',max_length=20,default='',
#         validators=[validators.RegexValidator(regex=r'^\d{7,11}$',message='请填写7到11位纯数字')]) 
#     bkgw = models.CharField(verbose_name='报考岗位',max_length=50,default='')
#     zyjszgz = models.CharField('取得的专业技术资格证',max_length=60,default='')
#     txdz = models.CharField(verbose_name='通信地址',max_length=100,default='')
#     dzyx = models.CharField(verbose_name='电子邮箱',max_length=50,default='')   
#     grjl = models.TextField(verbose_name='个人简历',max_length=1000,default='')  
#     jcqk = models.TextField(verbose_name='奖惩情况',max_length=1000,blank=True, default='')   
#     jtzycyqk = models.TextField('家庭主要成员情况',max_length=500,default='',blank=True)  

# class kaodiao(BaseKaoshi):
#     """
#     """
#     category = 1

#     class Meta:
#         verbose_name = "劳动合同"
#         verbose_name_plural = verbose_name

#     # 考生填写字段
#     tx = models.ImageField("头像",blank=True, null=True,upload_to=appname+'/avatar') 
#     xm   = models.CharField(verbose_name='姓名', max_length=10, default='', validators=[validators.MinLengthValidator(2),])
#     xb   = models.CharField(verbose_name='性别', max_length=1, default='',choices=CHOICE_XB) 
#     hf    = models.CharField(verbose_name='婚否',max_length=1,default='',choices=CHOICE_HF) 
#     lxdh = models.CharField(verbose_name='联系电话',max_length=20,default='',
#         validators=[validators.RegexValidator(regex=r'^\d{7,11}$',message='请填写7到11位纯数字')]) 
#     bkgw = models.CharField(verbose_name='报考岗位',max_length=50,default='')
#     mz   = models.CharField('民族', max_length=5, default='汉') 
#     zzmm = models.CharField(verbose_name='政治面貌', max_length=7, default='',choices=CHOICE_ZZMM)
#     xl = models.CharField('学历',max_length=4, default='',blank=True, choices=CHOICE_XL)
#     xw = models.CharField('学位',max_length=4, default='',blank=True, choices=CHOICE_XW)
#     bysj = models.DateField('毕业时间',blank=True, null=True)
#     byyx = models.CharField('毕业院校',max_length=50, default='')
#     zy   = models.CharField('专业',max_length=50, blank=True, default='')
#     stzk = models.CharField('身体状况', max_length=2, default='',choices=CHOICE_STZK)
#     cjgzsj = models.DateField('参加工作时间', blank=True, null=True)
#     xgzdwjgw = models.CharField('现工作单位及岗位', max_length=50, default='')
#     zgsj = models.CharField('取得相应的资格(职称)及时间',max_length=60,default='')
#     jtzz = models.CharField(verbose_name='家庭地址',max_length=100,default='')
#     grjl = models.TextField(verbose_name='个人简历',max_length=1000,default='')  
#     jcqk = models.TextField(verbose_name='奖惩情况',max_length=1000,blank=True, default='')   
#     jtzycyqk = models.TextField('家庭主要成员情况',max_length=500,default='',blank=True)  

