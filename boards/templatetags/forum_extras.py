"""boards/templatetags/forum_extras.py — Markdown 渲染与时间相对化"""
import re
from datetime import datetime, timedelta

from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def markdown(value):
    """轻量 Markdown 渲染：标题、引用、段落、加粗、斜体、列表、分隔符。

    为保持"墨韵西游"古风版面，将 Markdown 转为带语义 class 的 HTML，
    以便 styles.css 中的 .article-content 样式生效。
    """
    if not value:
        return ''
    text = value

    # 转义 HTML
    text = (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )

    lines = text.split('\n')
    html = []
    in_quote = False
    quote_buf = []

    def flush_quote():
        nonlocal in_quote, quote_buf
        if quote_buf:
            html.append('<blockquote>' + '<br>'.join(quote_buf) + '</blockquote>')
            quote_buf = []
        in_quote = False

    for raw in lines:
        line = raw.rstrip()

        # 分隔符 ◆ ◆ ◆ 或 --- 转为墨韵分隔
        if re.match(r'^(-{3,}|\*{3,}|◆.*◆)$', line.strip()):
            flush_quote()
            html.append('<div class="ink-divider">◆ ◆ ◆</div>')
            continue

        # 标题
        m = re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            flush_quote()
            level = len(m.group(1))
            html.append(f'<h{level}>{_inline(m.group(2))}</h{level}>')
            continue

        # 引用块
        if line.startswith('>'):
            in_quote = True
            quote_buf.append(_inline(line.lstrip('>').strip()))
            continue
        else:
            flush_quote()

        # 空行
        if not line.strip():
            html.append('')
            continue

        # 普通段落
        html.append(f'<p>{_inline(line)}</p>')

    flush_quote()
    return mark_safe('\n'.join(html))


def _inline(text):
    """行内格式：加粗、斜体、行内代码"""
    # 加粗 **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # 斜体 *text*
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


@register.filter
def time_ago(value):
    """相对时间：3 小时前 / 2 天前 / 日期"""
    if not value:
        return ''
    now = timezone.now()
    if timezone.is_aware(value):
        now = timezone.now()
    diff = now - value
    seconds = diff.total_seconds()

    if seconds < 60:
        return '刚刚'
    if seconds < 3600:
        return f'{int(seconds // 60)} 分钟前'
    if seconds < 86400:
        return f'{int(seconds // 3600)} 小时前'
    if seconds < 604800:
        return f'{int(seconds // 86400)} 天前'
    return value.strftime('%Y-%m-%d')


@register.filter
def excerpt_of(post, length=80):
    """从帖子生成摘要"""
    if post.excerpt:
        return post.excerpt[:length]
    # 去除 Markdown 标记
    text = re.sub(r'[#>*`]', '', post.content)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:length] + ('…' if len(text) > length else '')


@register.simple_tag
def url_replace(request, field, value):
    """分页时保留其他查询参数"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
