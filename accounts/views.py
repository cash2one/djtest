import re
import datetime
import random

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.generic import View
from django.utils.translation import ugettext as _
from django.utils.timezone import now as datetime_now
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.utils.http import base36_to_int, is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from django.template.response import TemplateResponse 
from django.shortcuts import resolve_url,render_to_response, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, QueryDict, Http404
from django.forms.models import model_to_dict
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import (REDIRECT_FIELD_NAME, authenticate, get_user_model, login as auth_login, logout as auth_logout)
from django.conf import settings

from .forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from common.classviews import ModelView, FormView, TemplateView, DetailView, ListView, CreateView, UpdateView

User = get_user_model()

def is_login(request):
    if not request.is_ajax():
        raise Http404
    if request.user.is_authenticated():
        return JsonResponse({'status':'login'})
    return JsonResponse({'status':'logout'})

class UserProfile(TemplateView):
    template_name = 'accounts/profile.html'

profile = login_required(UserProfile.as_view())

class LoginMixin(object):

    appname = __file__.replace('\\','/').rsplit('/',2)[1]
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(
                request.META.get('HTTP_REFERER', settings.LOGIN_REDIRECT_URL))
        return super().dispatch(request, *args, **kwargs)

class UserCreate(LoginMixin, CreateView):

    model = User
    form_class = UserCreationForm

    def get_success_url(self):
        return reverse('accounts:activate_complete')

register = sensitive_post_parameters()(never_cache(UserCreate.as_view()))

class UserLogin(LoginMixin, FormView):

    form_class = AuthenticationForm
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        self.redirect_to = request.POST.get('next', request.GET.get('next', ''))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())        
        return super().form_valid(form)

    def get_success_url(self):
        if not is_safe_url(url=self.redirect_to, host=self.request.get_host()):
            self.redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return self.redirect_to      

login = sensitive_post_parameters()(csrf_protect(never_cache(UserLogin.as_view())))

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

class RegisterComplete(TemplateView):
    template_name = 'accounts/register_complete.html'

register_complete = RegisterComplete.as_view()

class PasswordReset(FormView):

    template_name = 'accounts/password_reset_form.html'
    form_class = PasswordResetForm
    token_generator     = default_token_generator
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accounts:password_reset_done')

password_reset = PasswordReset.as_view()

class PasswordResetDone(TemplateView):
    template_name = 'accounts/password_reset_done.html'

password_reset_done = PasswordResetDone.as_view()

class PasswordResetConfirm(FormView):

    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetPasswordForm
    token_generator = default_token_generator
    

    def dispatch(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')
        assert uidb64 is not None and token is not None 
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        self.user = user
        if user is not None and self.token_generator.check_token(user, token):
            self.validlink = True      
            return super().dispatch(request, *args, **kwargs)
        self.validlink = False
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['validlink'] = self.validlink
        return kwargs

    def get_success_url(self):
        return reverse('accounts:password_reset_complete')

password_reset_confirm = sensitive_post_parameters()(never_cache(PasswordResetConfirm.as_view()))

class PasswordResetComplete(TemplateView):

    template_name ='accounts/password_reset_complete.html'

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['login_url'] = resolve_url(settings.LOGIN_URL)
        return kwargs

password_reset_complete = PasswordResetComplete.as_view()


class PasswordChange(FormView):

    template_name = 'accounts/password_change_form.html'
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accounts:password_change_done')

password_change = sensitive_post_parameters()(login_required(PasswordChange.as_view()))

class PasswordChangeDone(TemplateView):

    template_name ='accounts/password_change_done.html'

    # def get_context_data(self, **kwargs):
    #     kwargs = super().get_context_data(**kwargs)
    #     return kwargs

password_change_done = login_required(PasswordChangeDone.as_view())


class Activate(TemplateView):

    template_name ='accounts/activate_fail.html'

    def get(self, request, *args, **kwargs):
        activation_key = kwargs.get('activation_key')
        user = User.objects.activate_user(activation_key)
        if user:
            return HttpResponseRedirect(reverse('accounts:activate_complete'))
        context = self.get_context_data()
        return self.render_to_response(context)

activate = Activate.as_view()

class ActivateComplete(TemplateView):

    template_name ='accounts/activate_complete.html'

activate_complete = ActivateComplete.as_view()

