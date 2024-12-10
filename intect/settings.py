"""
Django settings for intect project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-euz(35rb^7_^9(*@mru&95nnwr8v_adfb(2v+vv0!m8!+vro*1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# DEBUG = False # boto3のコメントアウトは不要

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig", # accountアプリ
    "infra.apps.InfraConfig",       # infraアプリ
    "storages", # pip install django-storages
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "intect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [ os.path.join(BASE_DIR, 'templates') ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "intect.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
if DEBUG:
        STATICFILES_DIRS = [ BASE_DIR / "static" ] # こことbase.htmlの「href="{% static 'infra/css/style.css' %}」の値を合わせてstyle.cssの読み込みを行う
    # BASE_DIR：C:\work\django\myproject\program\intect\
    
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

AUTH_USER_MODEL = 'accounts.CustomUser'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = 'list-article' # ログイン時に表示するページ
LOGOUT_REDIRECT_URL = '/'

if not DEBUG:
    # Herokuデプロイ時に必要になるライブラリのインポート
    import django_heroku
    import dj_database_url

    # ALLOWED_HOSTSにホスト名を入力
    ALLOWED_HOSTS = [ os.environ["HOST"] ]
    # CSRFトークンの生成、ハッシュ化に使われる。
    SECRET_KEY = os.environ["SECRET_KEY"]
    
    # 静的ファイル配信ミドルウェア（whitenoise）を使用　※順番不一致だと動かない
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
    
    # Herokuデータベースを使用
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME'    : os.environ["DB_NAME"],
                'USER'    : os.environ["DB_USER"],
                'PASSWORD': os.environ["DB_PASSWORD"],
                'HOST'    : os.environ["DB_HOST"],
                'PORT'    : '5432',
                }
            }
    
    # STATIC_ROOT         = "/var/www/{}/static".format(BASE_DIR.name)

    #下記はファイルのアップロード機能を有する場合のみ
    # MEDIA_ROOT          = "/var/www/{}/media".format(BASE_DIR.name)

    #import environ

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # env = environ.Env()
    # 環境変数の強制読み込みを行う
    # environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
    
    #DBのアクセス設定
    db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=True)
    DATABASES['default'].update(db_from_env)
    
    # 静的ファイル(static)の存在場所を指定する
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    # STATIC_ROOT = BASE_DIR / 'static'

    #ストレージ設定
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
    
    # mediaファイル保存先
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # 保存先URL
    S3_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME # http://(AWS_STORAGE_BUCKET_NAME).s3.amazonaws.com/
    MEDIA_URL = S3_URL
    # AWSの設定
    AWS_S3_FILE_OVERWRITE = False # 同じファイル名が存在した場合、上書きを行う(デフォルト:True)
    AWS_DEFAULT_ACL = None # アップロードされたオブジェクトのアクセスコントロールリストを指定(推奨 None:S3バケットのデフォルトACLが適用)