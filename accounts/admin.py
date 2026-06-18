"""accounts/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from accounts.models import Follow, Message, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '用户资料'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'recipient__username')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Follow)
admin.site.register(Message, MessageAdmin)
