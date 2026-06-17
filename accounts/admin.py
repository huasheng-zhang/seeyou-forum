"""accounts/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from accounts.models import Profile, Follow


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '用户资料'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Follow)
