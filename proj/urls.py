from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()
from django.views.generic import RedirectView
from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico',permanent=True)),

    url(r'^$', views.home, name='home'),
    url(r'^django/$', views.home, name='home'),
    # url(r'^$', cache_page(60 * 15)(views.home), name='home'),
    url(r'^guide/$', views.guide, name='guide'),
    url(r'^about/$', views.about, name='about'),
]


urlpatterns += [url(r'^django/%s/'%app, include('%s.urls'%app, namespace=app)) 
    for app in settings.INSTALLED_APPS if '.' not in app]

urlpatterns += [url(r'^%s/'%app, include('%s.urls'%app, namespace=app)) 
    for app in settings.INSTALLED_APPS if '.' not in app]

from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT )