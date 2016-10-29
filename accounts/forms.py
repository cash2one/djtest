import re
import warnings
from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.http import urlsafe_base64_encode
from django.utils.html import format_html, format_html_join
from django.utils.encoding import force_bytes
from django.template import loader
from django.forms.utils import flatatt
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError,ImproperlyConfigured
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import get_user_model, authenticate
from django import forms
from django.core import validators

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    class Meta:
        model = User
        fields = ('sfzh', 'email')
        error_messages={

        }
        widgets = {
            'sfzh': forms.TextInput(attrs={'placeholder':'请填写本人18位身份证号'}),
            'email':forms.TextInput(attrs={'placeholder':'请填写常用邮箱，用于找回密码'}),
        }
        labels = {
        }

    password1=forms.CharField(label="密码", max_length=128,widget=forms.PasswordInput)
    password2=forms.CharField(label="确认密码", max_length=128,widget=forms.PasswordInput)

    def clean_sfzh(self):
        sfzh = self.cleaned_data.get('sfzh','').upper()
        try:
            User._default_manager.get(sfzh=sfzh)
        except User.DoesNotExist:
            n = len(sfzh)
            if n!=18:
                 raise forms.ValidationError('身份证号需18位, 目前是%s位.'%n, )
            return sfzh
        raise forms.ValidationError('该身份证号已被注册',code='sfzh_duplicate')
        
    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User._default_manager.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('该邮箱已被注册',code='email_duplicate')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('两次输入的密码不一致',code='password_mismatch')
        if len(password2)<6:
            raise forms.ValidationError('密码至少6位数',code='password_too_short')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True
        if commit:
            user.save()
        return user

class AuthenticationForm(forms.Form):
    
    sfzh = forms.CharField(
        label      = "身份证号", 
        max_length = 18, 
        widget     = forms.TextInput(attrs={'placeholder':'请填写本人18位身份证号'}),
        validators = [
            validators.RegexValidator(r'^\d{17}[\dXx]$',message='格式不正确，需17位数字+1位数字或英文字母X'),
        ],
    )
    password = forms.CharField(
        label="密码", max_length=128, widget=forms.PasswordInput,
        validators=[
            validators.MinLengthValidator(6),
        ],
    )

    def clean(self):
        username = self.cleaned_data.get('sfzh','').upper()  
        password = self.cleaned_data.get('password')
        if username and password:
            self.user_cache = authenticate(username=username,password=password)
            if self.user_cache is None:
                raise forms.ValidationError( "账号或密码错误",code='invalid_login')
            elif not self.user_cache.is_active:
                raise forms.ValidationError("该账号未激活,无法登录",code='inactive')
        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class UserChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        return self.initial["password"]

class PasswordResetForm(forms.Form):
    "通过邮箱找回密码的表单"

    email = forms.EmailField(label=_("Email"), max_length=75)

    def save(self, 
             domain_override=None,
             subject_template_name='accounts/password_reset_subject.txt',
             email_template_name='accounts/password_reset_email.html',
             token_generator=default_token_generator,
             use_https=False, 
             from_email=None, 
             request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        
        email = self.cleaned_data["email"]
        active_users = User._default_manager.filter(email__iexact=email, is_active=True)
        for user in active_users:
            if not user.has_usable_password():
                continue
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'user': user,
                'protocol': 'https' if use_https else 'http',
                'reset_url':reverse('accounts:password_reset_confirm',kwargs={'uidb64':uid,'token':token})
            }
            subject = loader.render_to_string(subject_template_name, c)
            subject = ''.join(subject.splitlines())
            message = loader.render_to_string(email_template_name, c)
            user.email_user(subject, message, from_email)

class SetPasswordForm(forms.Form):
    """
    直接填写2个密码,提交后即可为该用户重设密码.
    A form that lets a user change set his/her password without entering the
    old password
    """
    error_messages = {
        'password_mismatch': "两次输入的新密码不一致",
        'password_too_short':"密码至少6位数",
    }
    new_password1 = forms.CharField(label="新密码",widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="新密码确认",widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        if len(password2)<6:
            raise forms.ValidationError(
                self.error_messages['password_too_short'],
                code='password_too_short',
            )
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class PasswordChangeForm(SetPasswordForm):
    """
    通过旧密码更改密码
    继承了密码重设的表格,密码更改表格相当于只是多了一个旧密码框.
    """
    error_messages = dict(SetPasswordForm.error_messages, **{
        'password_incorrect': "旧密码输入错误",
    })
    old_password = forms.CharField(label="旧密码",widget=forms.PasswordInput)

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

PasswordChangeForm.base_fields = OrderedDict([
    (k, PasswordChangeForm.base_fields[k])
    for k in ['old_password', 'new_password1', 'new_password2']
])

