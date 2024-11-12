from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from .views import SignupView
from accounts import views
from django.views.generic import TemplateView

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'), # next_pageにインデックスページを指定
    path('signup/', SignupView.as_view(), name='signup'),
    path('register/', views.register_view, name='register'), # アカウント作成ページ
    path('my_page/', views.my_page_view, name='my_page'), # マイページ
    path('my_page/<int:pk>/', views.MyPage.as_view(), name='my_page_detail'), # マイページの詳細
    path('awaiting_approval/', TemplateView.as_view(template_name='accounts/awaiting_approval.html'), name='awaiting_approval'), # 共通の認証待ちページ
]