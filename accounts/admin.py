from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Company

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password', 'is_active')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'company')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'company', 'password1', 'password2', 'is_active')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Company)