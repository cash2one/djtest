from django.contrib import admin
from .models import Config, hetong
# Register your models here.

class hetongAdmin(admin.ModelAdmin):
    list_filter = ('bkgw','check_status',)
    list_display = ('zkzh','xm','xb','creater','bkgw','bscj','bspm')

admin.site.register(hetong, hetongAdmin)

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('title','enable',)

admin.site.register(Config, ConfigAdmin)