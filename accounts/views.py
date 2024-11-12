from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import CreateView
from accounts.models import Company, CustomUser
from .forms import SignupForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm  # ユーザ登録用フォーム
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

class SignupView(CreateView):
    model = CustomUser
    form_class = SignupForm
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        company_name = form.cleaned_data.get('company_name')
        if company_name:
            company = Company.objects.filter(name=company_name).first()
            if not company:
                company = Company.objects.create(name=company_name)
            self.object.company = company
        self.object.is_active = False
        self.object.save()
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:awaiting_approval')
  
'''自分しかアクセスできないようにするMixin(My Pageのため)'''
class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self): # 今ログインしてるユーザーのpkと、そのマイページのpkが同じなら許可
        user = self.request.user # ログインしているユーザーを取得
        return user.pk == self.kwargs['pk'] # ログインしているユーザーのpkがURLに含まれるpkと一致するかチェック
        # 一致する場合、Trueを返す


'''マイページ'''
class MyPage(LoginRequiredMixin, OnlyYouMixin, generic.DetailView):
    model = CustomUser
    template_name = 'accounts/my_page.html'
    context_object_name = 'user'  # 明示的にユーザーオブジェクトを 'user' として使用
    # モデル名小文字(user)でモデルインスタンスがテンプレートファイルに渡される

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('accounts:my_page_detail', pk=user.pk) # アプリケーション名を含める
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def my_page_view(request):
    return redirect('accounts:my_page_detail', pk=request.user.pk)