"""accounts/views.py — 用户认证、个人主页、私信"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm, RegisterForm
from accounts.models import Follow, Message, Profile
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
    """登录（已登录用户访问时先登出，再显示登录页）"""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, '已登出，请重新登录。')
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
    is_mutual = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user, following=user
        ).exists()
        if is_following:
            is_mutual = Follow.objects.filter(
                follower=user, following=request.user
            ).exists()

    return render(request, 'user/profile.html', {
        'target_user': user,
        'profile': profile,
        'posts': page,
        'is_following': is_following,
        'is_mutual': is_mutual,
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


# ============================================================
# 私信
# ============================================================
def _are_mutual_following(u1, u2):
    """判断两个用户是否互相关注（互粉）"""
    return (
        Follow.objects.filter(follower=u1, following=u2).exists()
        and Follow.objects.filter(follower=u2, following=u1).exists()
    )


@login_required
def messages_inbox(request):
    """收件箱：会话列表（按最近消息排序）"""
    # 取出与当前用户有过私信的所有对方用户
    sent_to = User.objects.filter(
        received_messages__sender=request.user
    ).distinct()
    received_from = User.objects.filter(
        sent_messages__recipient=request.user
    ).distinct()
    partners = (sent_to | received_from).distinct()

    conversations = []
    for partner in partners:
        last_msg = (
            Message.objects.filter(
                Q(sender=request.user, recipient=partner)
                | Q(sender=partner, recipient=request.user)
            ).order_by('-created_at').first()
        )
        unread_count = Message.objects.filter(
            sender=partner, recipient=request.user, is_read=False
        ).count()
        conversations.append({
            'partner': partner,
            'last_msg': last_msg,
            'unread_count': unread_count,
        })
    # 按最近消息时间倒序
    conversations.sort(key=lambda c: c['last_msg'].created_at, reverse=True)

    # 互粉好友列表（用于发起新会话）
    following_ids = set(
        Follow.objects.filter(follower=request.user)
        .values_list('following_id', flat=True)
    )
    friends = User.objects.filter(
        pk__in=following_ids,
        follower_set__following=request.user,
    ).exclude(pk=request.user.pk).order_by('profile__display_name')

    return render(request, 'messages/inbox.html', {
        'conversations': conversations,
        'friends': friends,
        'active_nav': 'messages',
    })


@login_required
def messages_conversation(request, username):
    """与某用户的会话详情"""
    partner = get_object_or_404(User, username=username)
    if partner == request.user:
        return redirect('messages_inbox')

    # 权限校验：仅互粉用户可对话
    if not _are_mutual_following(request.user, partner):
        messages.error(request, '仅互相关注的取经人可以私信。先去关注对方吧。')
        return redirect('profile', username=username)

    # 取出两人之间的全部消息
    msg_list = (
        Message.objects.filter(
            Q(sender=request.user, recipient=partner)
            | Q(sender=partner, recipient=request.user)
        ).order_by('created_at')
    )

    # 标记对方发来的未读消息为已读
    Message.objects.filter(
        sender=partner, recipient=request.user, is_read=False
    ).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=partner,
                content=content[:2000],
            )
            return redirect('messages_conversation', username=username)

    # 分页（每页 30 条，倒序，但模板里反转为正序显示）
    paginator = Paginator(msg_list, 30)
    page = paginator.get_page(request.GET.get('page'))

    # 互粉好友列表（侧边栏用）
    following_ids = set(
        Follow.objects.filter(follower=request.user)
        .values_list('following_id', flat=True)
    )
    friends = User.objects.filter(
        pk__in=following_ids,
        follower_set__following=request.user,
    ).exclude(pk=request.user.pk).order_by('profile__display_name')

    # 会话列表（侧边栏用）
    sent_to = User.objects.filter(
        received_messages__sender=request.user
    ).distinct()
    received_from = User.objects.filter(
        sent_messages__recipient=request.user
    ).distinct()
    partners = (sent_to | received_from).distinct()
    conversations = []
    for p in partners:
        last_msg = (
            Message.objects.filter(
                Q(sender=request.user, recipient=p)
                | Q(sender=p, recipient=request.user)
            ).order_by('-created_at').first()
        )
        if last_msg:
            unread = Message.objects.filter(
                sender=p, recipient=request.user, is_read=False
            ).count()
            conversations.append({
                'partner': p,
                'last_msg': last_msg,
                'unread_count': unread,
            })
    conversations.sort(key=lambda c: c['last_msg'].created_at, reverse=True)

    return render(request, 'messages/conversation.html', {
        'partner': partner,
        'messages': page,
        'friends': friends,
        'conversations': conversations,
        'active_nav': 'messages',
    })


@require_POST
@login_required
def messages_send(request, username):
    """发送私信（AJAX）"""
    partner = get_object_or_404(User, username=username)
    if partner == request.user:
        return JsonResponse({'ok': False, 'error': '不能给自己发私信'}, status=400)

    if not _are_mutual_following(request.user, partner):
        return JsonResponse(
            {'ok': False, 'error': '仅互相关注的取经人可以私信'}, status=403
        )

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'ok': False, 'error': '内容不能为空'}, status=400)

    msg = Message.objects.create(
        sender=request.user,
        recipient=partner,
        content=content[:2000],
    )

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({
            'ok': True,
            'message': {
                'id': msg.id,
                'content': msg.content,
                'time': '刚刚',
                'sender': request.user.profile.display_name,
                'avatar_char': request.user.profile.avatar_char,
                'avatar_class': request.user.profile.avatar_class,
            },
        })
    return redirect('messages_conversation', username=username)
