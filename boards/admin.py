"""boards/admin.py"""
from django.contrib import admin

from boards.models import Board, Post, Comment, Tag, Like, Favorite, Notice


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'board', 'is_essence', 'is_pinned',
                    'like_count', 'comment_count', 'created_at')
    list_filter = ('board', 'is_essence', 'is_pinned')
    search_fields = ('title', 'content', 'author__username')
    list_editable = ('is_essence', 'is_pinned')
    raw_id_fields = ('author',)


class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'en_name', 'sort_order',
                    'post_count', 'today_count')
    list_editable = ('sort_order',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'parent', 'like_count', 'created_at')
    search_fields = ('content', 'author__username')


admin.site.register(Board, BoardAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Tag)
admin.site.register(Like)
admin.site.register(Favorite)
admin.site.register(Notice)
