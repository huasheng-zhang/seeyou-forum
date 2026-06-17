"""accounts/views.py — 用户认证与个人主页"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.forms import LoginForm, RegisterForm
from accounts.models import Follow, Profile
from boards.models import Favorite, Post


def register_view(request):
    """注册"""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'欢迎加入西游论坛，{user.profile.display_name}！')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {
        'form': form,
        'active_nav': 'auth',
    })


def login_view(request):
    """登录"""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{user.profile.display_name}！')
                next_url = request.GET.get('next') or request.POST.get('next') or 'home'
                return redirect(next_url)
            else:
                form.add_error(None, '用户名或密码不正确')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {
        'form': form,
        'active_nav': 'auth',
    })


def logout_view(request):
    """登出"""
    logout(request)
    messages.info(request, '已登出，山高水远，后会有期。')
    return redirect('home')


def profile_view(request, username):
    """用户主页"""
    user = get_object_or_404(User, username=username)
    profile = user.profile
    posts = (
        Post.objects.filter(author=user)
        .select_related('board')
        .order_by('-created_at')
    )
    paginator = Paginator(posts, 10)
    page = paginator.get_page(request.GET.get('page'))

    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user, following=user
        ).exists()

    return render(request, 'user/profile.html', {
        'target_user': user,
        'profile': profile,
        'posts': page,
        'is_following': is_following,
        'is_self': request.user == user,
        'active_nav': 'profile',
    })


@login_required
def favorites_view(request, username):
    """我的收藏"""
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return redirect('profile', username=username)
    favs = (
        Favorite.objects.filter(user=user)
        .select_related('post', 'post__author', 'post__board')
        .order_by('-created_at')
    )
    paginator = Paginator([f.post for f in favs], 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'user/favorites.html', {
        'target_user': user,
        'posts': page,
        'active_nav': 'profile',
    })
