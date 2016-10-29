
"""ngo settings for proj project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from collections import OrderedDict


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\','/')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n7=u)otegv7@)z&*rvuabdefgqv5gtyhaw6j1yiq+-!ull9hfc'

ICP = 'abc'
ADMINS = [('as', 'yeah@qq.com')]
SERVER_EMAIL = 'djtest@163.com'

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# SESSION_CACHE_ALIAS = "default"

import platform
if 'indows' in platform.platform() or 'Darwin' in platform.platform():
    DEBUG = True
else:
    DEBUG = False

if DEBUG is True :
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }}
    # A list of locations of additional static files
    STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
else:
    DATABASES = {'default': {
        'ENGINE'  : 'django.db.backends.postgresql_psycopg2',
        'NAME'    : 'postgres',
        'USER'    : 'postgres',
        'PASSWORD': '',
        'HOST'    : '127.0.0.1',
        'PORT'    : '5432',
    }}
    STATIC_ROOT = os.path.join(BASE_DIR, "static").replace('\\','/')
    ALLOWED_HOSTS =  ['www.httper.cn','httper.cn']

# DEBUG = True

# Application definition

XIAN_CONTEXT = OrderedDict((
    ('jiangan', {
        'shen'   :'sichuan',
        'shi'    :'yibin',
        'xian'   :'jiangan',
        'shen_cn':'四川省',
        'shi_cn' :'宜宾市',
        'xian_cn':'江安县',}),
    # ('changning', {
    #     'shen'   :'sichuan',
    #     'shi'    :'yibin',
    #     'xian'   :'changning',
    #     'shen_cn':'四川省',
    #     'shi_cn' :'宜宾市',
    #     'xian_cn':'长宁县',}),
    # ('xingwen', {
    #     'shen'   :'sichuan',
    #     'shi'    :'yibin',
    #     'xian'   :'xingwen',
    #     'shen_cn':'四川省',
    #     'shi_cn' :'宜宾市',
    #     'xian_cn':'兴文县',}),

))

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'accounts',
    'pay',
    #'kaohe',
)+tuple(XIAN_CONTEXT)

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware', # 翻译中间件
)

ROOT_URLCONF = 'proj.urls'

WSGI_APPLICATION = 'proj.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

TEMPLATES = [
    {
        'BACKEND': 'common.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates')] + \
            [os.path.join(BASE_DIR, app +'/templates') for app in INSTALLED_APPS if '.' not in app],
        #'APP_DIRS': True,
        'OPTIONS': {
            #'environment':'my.template.environment',
            #'autoescape':False,
        },
    },

    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# --------ADD------------------------------------------------------------------
ACTIVATED = 'sec'
ACCOUNT_ACTIVATION_DAYS = 3
# whether in need of email activation in registeration,
USER_NEED_ACTIVATE = False
MAX_FAMILY_NUM = 5 # 报名表"主要家庭成员情况",最多允许填写的成员数量

# --------OVERRIDE-------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media').replace('\\','/')

AUTH_USER_MODEL = 'accounts.User'

# AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

LOGIN_URL = '/accounts/login/'

LOGOUT_URL = '/accounts/logout/'

LOGIN_REDIRECT_URL = '/' #'/accounts/'

SITE_ID = 1

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'djtest@163.com'
EMAIL_HOST_USER = 'djtest@163.com'
EMAIL_HOST_PASSWORD = '123456'
