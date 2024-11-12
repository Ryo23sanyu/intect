from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
       
class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="姓")
    last_name = forms.CharField(max_length=30, required=True, label="名")
    company_name = forms.CharField(max_length=100, required=False, label="会社名") # , help_text="姓を30文字以内で入力してください。"

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'company_name', 'password1', 'password2')
        labels = {
            'username': 'ユーザー名',
            'first_name': '名前',
            'last_name': '姓',
            'email': 'メールアドレス',
            'password1': 'パスワード',
            'password2': '確認用パスワード',
        }