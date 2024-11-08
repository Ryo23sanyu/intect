from django.db import models
from infra.models import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Company(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# ユーザー名をアルファベット、数字、漢字、カタカナ、ひらがな対応にする
username_validator = RegexValidator(
    regex=r'^[\w.@+-ぁ-ヶ一-龥々ー\\s]*$',
    message='ユーザー名には、アルファベット、数字、@/./+/-/_/ひらがな/カタカナ/漢字しか使用できません。'
)

class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True, # ユニーク制約(重複禁止)を設定
        validators=[username_validator], # カスタムバリデータを追加
        error_messages={
            'unique': "このユーザー名はすでに使用されています。",
        },
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_customuser_set',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_customuser_set',
        blank=True,
        help_text='Specific permissions for this user.'
    )
