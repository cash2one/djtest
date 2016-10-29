import re
import os
from jinja2 import Template
from datetime import date

from django.utils.safestring import mark_safe
from collections import OrderedDict
from django.forms.widgets import ClearableFileInput
from django.forms.models import model_to_dict
from django.forms.fields import ImageField
from django.core.validators import BaseValidator
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError,ImproperlyConfigured
from django import forms

from . import models

cd = os.path.dirname(__file__)

HINT_GRJL = 'X年X月-X年X月,就读于XX大学\nX年X月-X年X月,就职于XX公司XX职位'
HINT_JCQK = 'X年X月, 获得XX奖励\nX年X月, 受到XX处罚'

HINT_BKGW='''\
按"岗位名称,招录数"格式填写,多个岗位换行.例如:
乡镇协理员,2
警务辅助人员,3'''.replace('\r\n','\n')

HINT_BSMENU = '''\
按"时间,地点,考试科目"格式填写,多个科目换行,例如:
2015年7月25日 上午8:30-10:00, 政府大楼三楼二会议室, 行测
2015年7月25日 下午14:00-17:00, 政府大楼三楼二会议室, 申论'''

HINT_BBSGW='''\
多个岗位换行.例如:
乡镇协理员
警务辅助人员'''.replace('\r\n','\n')

HINT_SPECIAL_RULES='''\
此次考试的特别规定, 作为考试规则的补充.多条规定换行表示.
每条规定之前不必使用序号, 例如:

考生应提前一天查明交通路线
技能测试的考生注意事项参照公告执行'''

HINT_FAMILY = '''\
按"姓名, 称谓, 工作单位, 职务"格式填写,逗号分隔,
多个成员换行,没有的项目填'无',例如:

父亲,李四,乙企业,总经理
母亲,张三,甲公司,办公室主任
弟弟,李五,无,无'''.replace('\r\n','\n')


class AvatarInput(ClearableFileInput):

    template_with_initial = '<img class="avatar" src="%(initial_url)s"></img> %(input)s'


class AvatarField(ImageField):
    widget = AvatarInput

class BaomingForm(forms.ModelForm):

    '''
    报名表格基类, 实现了以下特殊需求:
    1.初始参数增加config
    2.字段bkgw的choices参数根据config动态确定;
    3.字段tx是自定义的, 创建时必须上传tx, 更新时不必.可限制tx的比例和大小
    4.更改默认的必填项提示信息.
    '''
    class Meta:
        abstract = True

    TX_SIZE_LIMIT = 1#False
    TX_RATE_LIMIT = 1#False
    TX_MAXSIZE_KB = 50
    TX_RATE_RANGE = (0.65, 0.75) # 长宽比限制

    tx = AvatarField(label="头像",required=False)

    # bkgw必须覆盖model的bkgw，否则在__init__中动态定义choices属性的成员无法保存在数据库
    bkgw = forms.ChoiceField(label="报考岗位") 

    def __init__(self, config, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fields['bkgw'].choices=(('',''),)+tuple((k,k) for k, v in config.bkgw.items())
        #self.fields['lxdh'].validators.append()
        for field in self.fields.values():
            field.error_messages['required'] = '您还没填写 %s '%field.label

    def clean_tx(self):
        value = self.cleaned_data['tx']
        if not value:
            if self.instance.pk is None:
                # 创建报名信息时头像不允许为空
                raise forms.ValidationError('请上传头像')
        elif hasattr(value, 'size') and hasattr(value,'image'):
            if self.TX_SIZE_LIMIT:
                size = round(value.size/1024, 1)
                if  size > self.TX_MAXSIZE_KB:
                    msg = '头像不能超过%sKB(目前%sKB)'%(self.TX_MAXSIZE_KB,size)
                    self.add_error('tx', msg)
            if self.TX_RATE_LIMIT:
                wd, ht = value.image.size
                r0, r1 = self.TX_RATE_RANGE
                rate = round(wd/ht, 2)
                if not (r0 < rate < r1):
                    msg = '头像宽高比应保持在%s到%s之间,目前比例%s(宽度%s,高度%s)'%(r0,r1,rate,wd,ht)
                    self.add_error('tx',msg)
        # else:
        #     # 当一个之前上传了头像的考生,更新信息时,如果没有上传头像,cleaned_data仍然会读取旧头像,
        #     # 而且这个头像对象不包含image属性, 真是莫名其妙
        #     print('value is not None, but no size and image attributes')
        return value

class ConfigForm(forms.ModelForm):

    class Meta:
        model = models.Config
        fields = ('enable','title','url','model_name', 'fee',
            'jingzheng_rate','bscj_rate','mscj_rate','bkgw',
            'bbsgw','bsmenu','special_rules','submit0','submit1','pay0','pay1','detail0','detail1',
            'zkz0', 'zkz1','bscj0','bscj1','all0','all1','article',
        )
        error_messages={
            'title':{'min_length':'至少输入%(limit_value)d个字符(已输入%(show_value)d个). '},
        }
        widgets = {
            'bbsgw': forms.Textarea(attrs={'title':HINT_BBSGW,'placeholder':HINT_BBSGW,'rows':5,}),
            'bsmenu':forms.Textarea(attrs={'title':HINT_BSMENU,'placeholder':HINT_BSMENU,'rows':5,}),
            'bkgw':forms.Textarea(attrs={'title':HINT_BKGW,'placeholder':HINT_BKGW,'rows':5,}),
            'special_rules':forms.Textarea(attrs={'title':HINT_SPECIAL_RULES,'placeholder':HINT_SPECIAL_RULES,'rows':5,}),
        }
        labels = {
            'bsmenu': '考试时间、地点和科目',
        }

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fields['url'].required = False
        self.fields['bbsgw'].required = False


class hetong(BaomingForm):
    "公开考调表格"
    class Meta:
        model = models.hetong
        fields = (
            "tx","xm","xb","hjszd","kssf",  "hf","lxdh","bkgw","mz","zzmm","xl","xw","bysj","byyx","zy","stzk","zc","zgzs",
            "cjgzsj","xgzdwjgw","zgsj","jtzz","grjl","jcqk","jtzycyqk",
        )
        error_messages={
            'xm':{'max_length':'最多输入%(limit_value)d个字符(已输入%(show_value)d个). ',
                  'min_length':'至少输入%(limit_value)d个字符(已输入%(show_value)d个). '},
        }
        widgets = {
            'jtzycyqk':forms.Textarea(attrs={'title':HINT_FAMILY, 'placeholder':HINT_FAMILY,'rows':7,}),
            'jcqk':forms.Textarea(attrs={'title':HINT_JCQK,'placeholder':HINT_JCQK,'rows':5,}),
            'grjl':forms.Textarea(attrs={'title':HINT_GRJL,'placeholder':HINT_GRJL,'rows':5,}),    
            'lxdh':forms.TextInput(attrs={'placeholder':'请填写7到11位数字',}),
            'hjszd':forms.TextInput(attrs={'placeholder':'请填写户籍所在地, 和户口簿信息一致',}),
            'bysj':forms.TextInput(attrs={'title':'示例:2010-12-31','placeholder':'示例:2010-12-31',}),
            'zgsj':forms.TextInput(attrs={'title':'岗位没有要求的可以不填','placeholder':'岗位没有要求的可以不填',}),
            'zgzs':forms.TextInput(attrs={'title':'如:教师资格证','placeholder':'如:教师资格证',}),
        }
        labels = {
            'zc': '有何专长',
            'zgzs':'有何资格证书',
            'zgsj':'取得相应的资格(职称)及时间',
        }

