"""boards/views.py — 论坛核心视图"""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Profile
from boards.forms import PostForm, CommentForm
from boards.models import Board, Comment, Favorite, Like, Notice, Post, Tag


# ============================================================
# 首页
# ============================================================
def home(request):
    """首页：Hero、六洞天、本期精华、新帖流转、侧栏"""
    # 板块
    boards = list(Board.objects.all().order_by('sort_order', 'id'))

    # 精华：1 头条 + 4 侧栏
    essence_qs = Post.objects.filter(is_essence=True).select_related(
        'author', 'board', 'author__profile'
    )
    feature_post = essence_qs.first()
    side_posts = essence_qs.exclude(pk=feature_post.pk)[:4] if feature_post else []

    # 最新帖子
    latest_posts = (
        Post.objects.select_related('author', 'board', 'author__profile')
        .order_by('-is_pinned', '-created_at')[:6]
    )

    # 取经人榜（按积分）
    top_users = (
        Profile.objects.select_related('user')
        .order_by('-score')[:5]
    )

    # 热门标签
    hot_tags = Tag.objects.order_by('-count')[:9]

    # 公告
    notices = Notice.objects.filter(is_active=True)[:4]

    # 全站统计
    today = timezone.now() - timedelta(days=1)
    stats = {
        'members': Profile.objects.count(),
        'posts': Post.objects.count(),
        'boards': Board.objects.count(),
        'today_posts': Post.objects.filter(created_at__gte=today).count(),
    }

    return render(request, 'index.html', {
        'boards': boards,
        'feature_post': feature_post,
        'side_posts': side_posts,
        'latest_posts': latest_posts,
        'top_users': top_users,
        'hot_tags': hot_tags,
        'notices': notices,
        'stats': stats,
        'active_nav': 'home',
    })


# ============================================================
# 板块页
# ============================================================
def board_detail(request, slug):
    """板块详情：帖子列表，支持排序与分页"""
    board = get_object_or_404(Board, slug=slug)
    sort = request.GET.get('sort', 'new')

    posts = Post.objects.filter(board=board).select_related(
        'author', 'author__profile'
    )
    if sort == 'hot':
        posts = posts.order_by('-like_count', '-comment_count', '-created_at')
    elif sort == 'essence':
        posts = posts.filter(is_essence=True).order_by('-created_at')
    else:  # new
        posts = posts.order_by('-is_pinned', '-created_at')

    paginator = Paginator(posts, 10)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'board.html', {
        'board': board,
        'posts': page,
        'sort': sort,
        'active_nav': 'boards',
    })


# ============================================================
# 帖子详情
# ============================================================
def post_detail(request, pk):
    """帖子详情：正文 + 评论 + 作者卡"""
    post = get_object_or_404(
        Post.objects.select_related('author', 'board', 'author__profile'),
        pk=pk,
    )

    # 浏览量 +1（同一会话内不重复）
    session_key = f'viewed_post_{pk}'
    if not request.session.get(session_key):
        Post.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
        request.session[session_key] = True
        request.session.modified = True
        post.refresh_from_db()

    # 评论：顶层评论 + 一级回复
    top_comments = (
        post.comments.filter(parent__isnull=True)
        .select_related('author', 'author__profile')
        .prefetch_related('replies', 'replies__author', 'replies__author__profile')
    )

    # 当前用户的点赞/收藏状态
    liked = False
    favorited = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post).exists()
        favorited = Favorite.objects.filter(user=request.user, post=post).exists()

    # 作者其他文章
    author_posts = (
        Post.objects.filter(author=post.author)
        .exclude(pk=pk)
        .order_by('-created_at')[:3]
    )

    # 相关帖子（同板块）
    related_posts = (
        Post.objects.filter(board=post.board)
        .exclude(pk=pk)
        .order_by('-like_count')[:4]
    )

    comment_form = CommentForm()

    return render(request, 'post.html', {
        'post': post,
        'top_comments': top_comments,
        'liked': liked,
        'favorited': favorited,
        'author_posts': author_posts,
        'related_posts': related_posts,
        'comment_form': comment_form,
        'active_nav': 'boards',
    })


# ============================================================
# 发帖 / 编辑
# ============================================================
@login_required
def post_create(request):
    """发帖"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            # 更新作者与板块计数
            _bump_counts(post)
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'post_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'boards',
    })


@login_required
def post_edit(request, pk):
    """编辑帖子（仅作者）"""
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_staff:
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post.pk)
    else:
        initial = {'tags_input': ' '.join(t.name for t in post.tags.all())}
        form = PostForm(instance=post, initial=initial)

    return render(request, 'post_form.html', {
        'form': form,
        'is_edit': True,
        'post': post,
        'active_nav': 'boards',
    })


# ============================================================
# 搜索
# ============================================================
def search(request):
    """全文搜索：标题/正文/作者"""
    q = request.GET.get('q', '').strip()
    board_filter = request.GET.get('board', '')
    posts = Post.objects.none()
    if q:
        posts = Post.objects.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(author__username__icontains=q) |
            Q(author__profile__display_name__icontains=q)
        ).select_related('author', 'board', 'author__profile')
        if board_filter:
            posts = posts.filter(board__slug=board_filter)
        posts = posts.order_by('-created_at')

    paginator = Paginator(posts, 10)
    page = paginator.get_page(request.GET.get('page'))
    boards = Board.objects.all()

    return render(request, 'search.html', {
        'q': q,
        'posts': page,
        'boards': boards,
        'board_filter': board_filter,
        'active_nav': 'search',
    })


# ============================================================
# AJAX 交互 API
# ============================================================
@require_POST
@login_required
def toggle_like(request, pk):
    """点赞 / 取消点赞"""
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if created:
        Post.objects.filter(pk=pk).update(like_count=F('like_count') + 1)
        liked = True
    else:
        like.delete()
        Post.objects.filter(pk=pk).update(like_count=F('like_count') - 1)
        liked = False
    post.refresh_from_db()
    return JsonResponse({'liked': liked, 'count': post.like_count})


@require_POST
@login_required
def toggle_favorite(request, pk):
    """收藏 / 取消收藏"""
    post = get_object_or_404(Post, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, post=post)
    if created:
        Post.objects.filter(pk=pk).update(favorite_count=F('favorite_count') + 1)
        favorited = True
    else:
        fav.delete()
        Post.objects.filter(pk=pk).update(favorite_count=F('favorite_count') - 1)
        favorited = False
    post.refresh_from_db()
    return JsonResponse({'favorited': favorited, 'count': post.favorite_count})


@require_POST
@login_required
def post_comment(request, pk):
    """发表评论（支持 AJAX 与表单提交）"""
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if not form.is_valid():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        return redirect('post_detail', pk=pk)

    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    parent_id = request.POST.get('parent_id')
    if parent_id:
        try:
            comment.parent = Comment.objects.get(pk=parent_id, post=post)
        except Comment.DoesNotExist:
            pass
    comment.save()
    Post.objects.filter(pk=pk).update(comment_count=F('comment_count') + 1)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.profile.display_name,
                'avatar_char': comment.author.profile.avatar_char,
                'avatar_class': comment.author.profile.avatar_class,
                'time': '刚刚',
                'parent_id': parent_id,
            },
        })
    return redirect('post_detail', pk=pk)


@require_POST
@login_required
def toggle_follow(request, username):
    """关注 / 取消关注"""
    from django.contrib.auth.models import User
    from accounts.models import Follow

    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'ok': False, 'error': '不能关注自己'}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=target
    )
    if created:
        Profile.objects.filter(user=request.user).update(
            following_count=F('following_count') + 1
        )
        Profile.objects.filter(user=target).update(
            follower_count=F('follower_count') + 1
        )
        following = True
    else:
        follow.delete()
        Profile.objects.filter(user=request.user).update(
            following_count=F('following_count') - 1
        )
        Profile.objects.filter(user=target).update(
            follower_count=F('follower_count') - 1
        )
        following = False

    target.profile.refresh_from_db()
    return JsonResponse({
        'following': following,
        'followers_count': target.profile.follower_count,
    })


# ============================================================
# 辅助函数
# ============================================================
def _bump_counts(post):
    """发帖后更新作者与板块计数"""
    Profile.objects.filter(user=post.author).update(
        post_count=F('post_count') + 1,
        score=F('score') + 10,
    )
    Board.objects.filter(pk=post.board.pk).update(
        post_count=F('post_count') + 1,
        today_count=F('today_count') + 1,
    )
    if post.is_essence:
        Profile.objects.filter(user=post.author).update(
            essence_count=F('essence_count') + 1,
            score=F('score') + 50,
        )
