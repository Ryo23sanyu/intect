from celery import Celery
import os

# DJANGO_SETTINGS_MODULE のパスを設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intect.settings')
# 　　　　　　　　　　　　　　　　　　　　　　　　　　　 ↑　プロジェクト名
# Celery アプリケーションのインスタンスを作成
app = Celery('intect')
# 　　　　 　　　 ↑　プロジェクト名
# Django の settings.py ファイルから Celery 設定を読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# インストールされている Django アプリケーションからタスクを自動検出
app.autodiscover_tasks()