"""boards/models.py — 板块、帖子、评论、标签、点赞、收藏、公告"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Board(models.Model):
    """板块：六洞天"""

    name = models.CharField('板块名', max_length=50)
    slug = models.SlugField(unique=True, max_length=80)
    icon = models.CharField('单字图标', max_length=2)
    en_name = models.CharField('英文名', max_length=80)
    description = models.TextField('描述')
    sort_order = models.IntegerField('排序', default=0)
    post_count = models.IntegerField('帖子数', default=0)
    today_count = models.IntegerField('今日新帖', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '板块'
        verbose_name_plural = '板块'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.en_name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """标签"""

    name = models.CharField('标签名', max_length=20, unique=True)
    count = models.IntegerField('引用数', default=0)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['-count', 'name']

    def __str__(self):
        return self.name


class Post(models.Model):
    """帖子"""

    title = models.CharField('标题', max_length=200)
    subtitle = models.CharField('副标题', max_length=200, blank=True)
    excerpt = models.TextField('摘要', max_length=500, blank=True)
    content = models.TextField('正文（Markdown）')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name='posts'
    )
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    is_essence = models.BooleanField('精华', default=False)
    is_pinned = models.BooleanField('置顶', default=False)
    cover = models.ImageField('封面', upload_to='covers/', blank=True, null=True)
    cover_url = models.URLField('封面外链', blank=True)
    view_count = models.IntegerField('浏览', default=0)
    like_count = models.IntegerField('点赞', default=0)
    comment_count = models.IntegerField('评论', default=0)
    favorite_count = models.IntegerField('收藏', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    @property
    def cover_image(self):
        """优先使用上传封面，其次外链，最后默认水墨图"""
        if self.cover:
            return self.cover.url
        if self.cover_url:
            return self.cover_url
        return (
            'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image'
            '?prompt=Chinese%20ink%20wash%20painting%20mountain%20mist%20'
            'sumi-e%20vermillion%20seal%20minimal&image_size=landscape_16_9'
        )


class Comment(models.Model):
    """评论（支持嵌套）"""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
    )
    content = models.TextField('内容')
    like_count = models.IntegerField('点赞', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username}：{self.content[:20]}'


class Like(models.Model):
    """点赞（帖子或评论）"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post, null=True, blank=True, on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, null=True, blank=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        unique_together = [('user', 'post'), ('user', 'comment')]


class Favorite(models.Model):
    """收藏"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
        unique_together = ('user', 'post')


class Notice(models.Model):
    """论坛公告"""

    NOTICE_TAGS = [
        ('活动', '活动'),
        ('版务', '版务'),
        ('更新', '更新'),
        ('招募', '招募'),
    ]

    tag = models.CharField('标签', max_length=10, choices=NOTICE_TAGS)
    content = models.CharField('内容', max_length=200)
    link = models.URLField('链接', blank=True)
    is_active = models.BooleanField('生效', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '公告'
        verbose_name_plural = '公告'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.tag}] {self.content[:30]}'
