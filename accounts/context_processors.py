"""accounts/context_processors.py — 注入当前用户资料到模板上下文"""
import django

from accounts.models import Profile


def user_profile(request):
    """为已登录用户注入 profile；游客注入 None"""
    if not request.user.is_authenticated:
        return {'current_profile': None, 'django_version': django.get_version()}
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        profile = Profile.objects.create(
            user=request.user,
            display_name=request.user.username,
        )
    return {
        'current_profile': profile,
        'django_version': django.get_version(),
    }
