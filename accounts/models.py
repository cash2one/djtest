import datetime
import hashlib
import random
import re

from django.conf import settings
from django.db import models
from django.core import validators
from django.core.mail import send_mail
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    datetime_now = datetime.datetime.now

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class UserManager(BaseUserManager):
    def _create_user(self, email, sfzh, password, is_active, is_staff, is_superuser,**extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('电子邮箱是必须的')
        email = self.normalize_email(email)
        user = self.model(
            email        = email,
            sfzh         = sfzh,
            is_active    = is_active,
            is_staff     = is_staff, 
            is_superuser = is_superuser,
            last_login   = now, 
            date_joined  = now, 
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)  
        return user

    def create_user(self, email, sfzh, password, **extra_fields):
        user = self._create_user(email, sfzh, password,True,False,False,**extra_fields)
        return user

    def create_superuser(self, email, sfzh, password, **extra_fields):
        return self._create_user(email, sfzh, password, True, True, True,**extra_fields)     

class User(AbstractBaseUser):

    class Meta:
        verbose_name = "注册用户"
        verbose_name_plural = '注册用户'
        
    objects = UserManager()        
    USERNAME_FIELD = 'sfzh'
    REQUIRED_FIELDS = ['email']

    email = models.EmailField('电子邮箱',max_length=75,unique=True,db_index=True,)
    sfzh = models.CharField('身份证号', max_length=18,unique=True,)
    is_active = models.BooleanField('是否激活', default=False,)
    is_staff = models.BooleanField('是否员工', default=False,)
    is_superuser = models.BooleanField('是否超级用户', default=False,)
    perm = models.CharField('权限', max_length=18,default='ordinary')
    date_joined = models.DateTimeField('注册时间',auto_now_add=True)

    def __str__(self):
        return str(self.sfzh)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
        
    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    @property
    def url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return reverse('accounts:profile',)

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

