"""boards/forms.py — 帖子与评论表单"""
from django import forms

from boards.models import Post, Comment, Tag


class PostForm(forms.ModelForm):
    """发帖/编辑帖子表单"""

    tags_input = forms.CharField(
        label='标签',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': '用空格分隔，例如：齐天大圣 取经路 水墨',
                'class': 'form-input',
            }
        ),
        help_text='最多 5 个标签，每个不超过 8 字',
    )

    class Meta:
        model = Post
        fields = ['title', 'subtitle', 'board', 'excerpt', 'content',
                  'cover_url', 'is_essence']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': '文章标题',
                    'class': 'form-input',
                    'maxlength': 200,
                }
            ),
            'subtitle': forms.TextInput(
                attrs={
                    'placeholder': '副标题（可选）',
                    'class': 'form-input',
                }
            ),
            'board': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': '摘要，用于列表展示（可选，留空则自动截取）',
                    'class': 'form-textarea',
                }
            ),
            'content': forms.Textarea(
                attrs={
                    'rows': 20,
                    'placeholder': '正文（支持 Markdown）…',
                    'class': 'form-textarea form-content',
                }
            ),
            'cover_url': forms.URLInput(
                attrs={
                    'placeholder': '封面图 URL（可选）',
                    'class': 'form-input',
                }
            ),
        }

    def clean_tags_input(self):
        raw = self.cleaned_data.get('tags_input', '')
        names = [n.strip() for n in raw.split() if n.strip()][:5]
        return names

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            # 处理标签
            names = self.cleaned_data.get('tags_input', [])
            post.tags.clear()
            for name in names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tag.count += 1
                tag.save()
                post.tags.add(tag)
        return post


class CommentForm(forms.ModelForm):
    """评论表单"""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': '且留一言，与君共话……（支持 Markdown）',
                    'class': 'form-textarea',
                }
            ),
        }
