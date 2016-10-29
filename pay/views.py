import random

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from . import notify_verify,  appname
from .models import order
# Create your views here.

def contextResponse(request,  template,  context):
    context.update({
            'getattr':getattr,
            'user'      : request.user, 
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL' : settings.MEDIA_URL,
            'DEBUG'     : settings.DEBUG,
            'url'       : lambda viewname, **kwargs : reverse(viewname, kwargs=kwargs),           
            'static'    : staticfiles_storage.url,
            'rand'      : lambda:random.randint(1,100),
            'appname'   : appname,
            'ICP':getattr(settings, 'ICP', ''), 
        })
    return TemplateResponse(request,  template,  context)

def payment_success(request):
    return contextResponse(
        request  = request,
        template = 'pay/payment_success.html',
        context  = {},
    )

def payment_error(request):
    return contextResponse(
        request  = request,
        template = 'pay/payment_error.html',
        context  = {},
    )

def return_url_handler(request):
    """
    Handler for synchronous updating billing information.
    """
    if notify_verify(request.GET):
        return HttpResponseRedirect(reverse('pay:payment_success'))
    return HttpResponseRedirect(reverse('pay:payment_error'))


from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def notify(request, model=order):
    """
    Handler for notify_url for asynchronous updating billing information.
    Logging the information.
    """
    if request.method == 'POST':
        if notify_verify(request.POST):
            out_trade_no = request.POST.get('out_trade_no')
            trade_status = request.POST.get('trade_status')
            trade_no = request.POST.get('trade_no')
            bill = model.objects.get(out_trade_no=out_trade_no)
            bill.trade_status = trade_status
            bill.trade_no = trade_no
            bill.save ()
            #print('passed notify check....',trade_status, type(trade_status))
            if trade_status == 'TRADE_SUCCESS' or trade_status == 'TRADE_FINISHED':
                obj = bill.get_object()
                if obj:
                    obj.is_pay = True
                    obj.save()
            return HttpResponse("success")
    return HttpResponse("fail")