from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

User = settings.AUTH_USER_MODEL
# Create your models here.
class order(models.Model):

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    creater = models.ForeignKey(User,verbose_name='付款人')

    app = models.CharField(verbose_name='区域名', max_length=100, default='')
    model_name = models.CharField(verbose_name='考试类型', max_length=100, default='')
    object_id = models.PositiveIntegerField(verbose_name='考试主键')

    out_trade_no = models.CharField(verbose_name='订单号', max_length=100, default='',unique=True)
    trade_no = models.CharField(verbose_name='流水号', max_length=100, default='')
    trade_status = models.CharField(verbose_name='交易状态', max_length=100, default='')

    def __str__(self):
        return self.out_trade_no

    def get_object(self):
        '根据app,model_name和pk尝试返回订单对应的对象.'
        try:
            model = ContentType.objects.get(app_label=self.app, model=self.model_name).model_class()
            obj = model.objects.get(pk=self.object_id)
            return obj
        except Exception as e:
            print(e)
            return None


    