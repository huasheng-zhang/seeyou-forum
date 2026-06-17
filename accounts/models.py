"""accounts/models.py — 用户资料与关注关系"""
from django.conf import settings
from django.db import models


class Profile(models.Model):
    """用户资料：扩展 Django auth User"""

    AVATAR_COLORS = [
        ('vermillion', '朱砂'),
        ('dark', '墨黑'),
        ('jade', '翡翠'),
        ('gold', '古铜'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField('显示名', max_length=30)
    role = models.CharField('身份', max_length=40, default='花果山 · 新客')
    avatar_char = models.CharField('头像单字', max_length=2, default='客')
    avatar_color = models.CharField(
        '头像配色', max_length=20, choices=AVATAR_COLORS, default='vermillion'
    )
    bio = models.TextField('简介', max_length=200, blank=True)
    post_count = models.IntegerField('文章数', default=0)
    follower_count = models.IntegerField('粉丝数', default=0)
    following_count = models.IntegerField('关注数', default=0)
    essence_count = models.IntegerField('精华数', default=0)
    score = models.IntegerField('积分', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return self.display_name

    @property
    def avatar_class(self):
        """对应模板中的头像配色 CSS 类"""
        mapping = {
            'vermillion': '',
            'dark': 'dark',
            'jade': 'jade',
            'gold': 'dark',
        }
        return mapping.get(self.avatar_color, '')


class Follow(models.Model):
    """关注关系：follower 关注 following"""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_set',
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '关注关系'
        verbose_name_plural = '关注关系'
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'
