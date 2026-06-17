# 西游论坛 · Seeyou Forum

> 取经路上，与君共话。
>
> 一个以《西游记》为精神底色的图文论坛，采用「墨韵西游」水墨风设计，
> 融合传统中式美学与现代编辑式排版。

![Django](https://img.shields.io/badge/Django-6.0.6-c83a2f?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13+-3776ab?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-c9a961)

---

## 项目简介

**西游论坛 Seeyou Forum** 是一个完整可用的生产级图文论坛应用，基于 Django MTV 架构构建。
论坛以《西游记》为精神底色，划分为「六洞天」六大板块，鼓励深度长文与图文创作。

### 设计风格

- **配色**：墨黑 / 宣纸米 / 朱砂红 / 古铜金 / 翡翠
- **字体**：Ma Shan Zheng（马善政毛笔）+ ZCOOL XiaoWei（站酷小薇）+ Noto Serif SC + Cormorant Garamond + DM Mono
- **美学**：水墨意象 + 朱砂印章 + 古风排版 + 编辑式网格

### 六洞天板块

| 板块 | 英文 slug | 图标 | 定位 |
|---|---|---|---|
| 取经问道 | `scripture` | 问 | 研读经典，问道取经。长文深度为主 |
| 花果山 | `flower-fruit` | 果 | 水帘洞内，闲话家常。生活趣事日常 |
| 天宫广记 | `heavenly-annals` | 天 | 天庭广记，仙班轶事。神话传说考据 |
| 地府幽冥 | `underworld` | 幽 | 幽冥地府，生死之间。鬼神志怪文化 |
| 龙宫宝藏 | `dragon-treasury` | 龙 | 东海龙宫，宝藏奇珍。器物法宝考 |
| 蓬莱仙岛 | `penglai` | 仙 | 蓬莱仙岛，以墨会友。原创水墨影像 |

---

## 功能特性

### 核心功能

- **用户系统**：注册 / 登录 / 登出 / 个人主页 / Profile 扩展（笔名、头像、简介、积分）
- **关注关系**：用户之间可相互关注，粉丝数 / 关注数实时统计
- **帖子系统**：发帖 / 编辑 / 删除，支持 Markdown 排版、副标题、摘要、封面图、标签
- **评论系统**：支持嵌套回复（一级），AJAX 无刷新发表
- **互动系统**：点赞 / 收藏 / 评论 / 关注，全部 AJAX 实现，CSRF 保护
- **板块系统**：六洞天，支持按最新 / 热门 / 精华排序，分页浏览
- **全文搜索**：标题 / 正文 / 作者名 / 笔名检索，支持板块过滤
- **浏览统计**：基于 session 的防重复浏览计数
- **公告系统**：论坛公告（活动 / 版务 / 更新 / 招募）
- **管理后台**：Django Admin 全功能管理（含 Profile 内联、置顶 / 精华快捷设置）
- **初始化数据**：`seed_data` 命令一键填充演示数据

### 技术亮点

- **轻量 Markdown 渲染**：自定义模板标签 `markdown`，支持标题 / 引用 / 加粗 / 斜体 / 代码 / 墨韵分隔符，无需第三方依赖
- **相对时间**：自定义 `time_ago` 过滤器（刚刚 / N 分钟前 / N 小时前 / N 天前 / 日期）
- **上下文处理器**：全局注入 `current_profile` 与 `django_version`
- **会话浏览计数**：同一会话内不重复计数，避免刷新刷量
- **响应式布局**：桌面 / 平板 / 移动端自适应
- **滚动入场动画**：IntersectionObserver 实现 `.reveal` 元素渐入
- **目录自动生成**：文章页根据 h2/h3 自动生成右侧目录，滚动高亮当前章节

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | Django 6.0.6 |
| 数据库 | SQLite（开发）/ PostgreSQL（生产可选） |
| 模板引擎 | Django Templates |
| 用户认证 | Django auth + Profile 扩展（OneToOneField） |
| 前端 | 原生 HTML / CSS / JavaScript（无构建步骤） |
| 图像处理 | Pillow（ImageField 支持） |
| Python | 3.13+ |

---

## 项目结构

```
seeyou-forum/
├── seeyou/                     # Django 项目配置
│   ├── settings.py             # 全局配置
│   ├── urls.py                 # 根路由
│   └── wsgi.py / asgi.py       # 部署入口
│
├── accounts/                   # 用户应用
│   ├── models.py               # Profile + Follow
│   ├── forms.py                # RegisterForm + LoginForm
│   ├── views.py                # 注册 / 登录 / 主页 / 收藏
│   ├── context_processors.py   # 全局注入 current_profile
│   └── admin.py                # ProfileInline 内联管理
│
├── boards/                     # 论坛核心应用
│   ├── models.py               # Board / Tag / Post / Comment / Like / Favorite / Notice
│   ├── views.py                # 首页 / 板块 / 帖子 / 搜索 / AJAX API
│   ├── forms.py                # PostForm + CommentForm
│   ├── templatetags/
│   │   └── forum_extras.py     # markdown / time_ago / excerpt_of / url_replace
│   ├── management/commands/
│   │   └── seed_data.py        # 初始化数据命令
│   └── admin.py                # 全模型后台管理
│
├── templates/                  # Django 模板
│   ├── base.html               # 基础模板（导航 / 页脚 / 消息 / 脚本）
│   ├── index.html              # 首页（Hero / 六洞天 / 精华 / 新帖 / 侧栏）
│   ├── post.html               # 帖子详情（正文 / 目录 / 作者卡 / 评论）
│   ├── board.html              # 板块页（排序 / 帖子列表 / 分页）
│   ├── search.html             # 搜索页（搜索框 / 结果 / 分页）
│   ├── post_form.html          # 发帖 / 编辑表单
│   ├── accounts/
│   │   ├── login.html          # 登录
│   │   └── register.html       # 注册
│   └── user/
│       ├── profile.html        # 个人主页
│       └── favorites.html      # 我的收藏
│
├── static/
│   └── styles.css              # 完整样式系统（墨韵西游设计）
│
├── manage.py                   # Django 管理脚本
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

---

## 快速开始

### 环境要求

- Python 3.13+
- pip

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/huasheng-zhang/seeyou-forum.git
cd seeyou-forum

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 执行数据库迁移
python manage.py migrate

# 5. 初始化演示数据（6 板块 / 5 用户 / 12 帖子 / 9 评论 / 10 关注 / 4 收藏）
python manage.py seed_data

# 6. 创建超级用户（用于管理后台）
python manage.py createsuperuser

# 7. 启动开发服务器
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 即可看到论坛首页。

### 测试账号

初始化数据后，以下账号可直接登录（密码均为 `seeyou12345`）：

| 用户名 | 笔名 | 身份 |
|---|---|---|
| `moyike` | 墨衣客 | 取经问道 · 主笔 |
| `qingshandu` | 青衫渡 | 蓬莱仙岛 · 画师 |
| `youminglu` | 幽冥录 | 地府幽冥 · 长文 |
| `shangjianmingyue` | 山间明月 | 花果山 · 散客 |
| `zangjinge` | 藏经阁主 | 取经问道 · 整理 |

管理后台：http://127.0.0.1:8000/admin/ （使用 `createsuperuser` 创建的账号）

---

## 路由总览

| 路径 | 视图 | 说明 |
|---|---|---|
| `/` | `home` | 首页 |
| `/board/<slug>/` | `board_detail` | 板块详情（支持 `?sort=new\|hot\|essence`） |
| `/post/<pk>/` | `post_detail` | 帖子详情 |
| `/post/new/` | `post_create` | 发帖（需登录） |
| `/post/<pk>/edit/` | `post_edit` | 编辑帖子（仅作者） |
| `/search/` | `search` | 全文搜索（支持 `?q=关键词&board=slug`） |
| `/accounts/login/` | `login_view` | 登录 |
| `/accounts/register/` | `register_view` | 注册 |
| `/accounts/logout/` | `logout_view` | 登出 |
| `/accounts/u/<username>/` | `profile_view` | 用户主页 |
| `/accounts/u/<username>/favorites/` | `favorites_view` | 我的收藏 |
| `/admin/` | Django Admin | 管理后台 |

### AJAX API（需登录，POST + CSRF）

| 路径 | 功能 | 返回 |
|---|---|---|
| `/api/post/<pk>/like/` | 点赞 / 取消点赞 | `{"liked": bool, "count": int}` |
| `/api/post/<pk>/favorite/` | 收藏 / 取消收藏 | `{"favorited": bool, "count": int}` |
| `/api/post/<pk>/comment/` | 发表评论（支持 `parent_id`） | `{"ok": bool, "comment": {...}}` |
| `/api/user/<username>/follow/` | 关注 / 取消关注 | `{"following": bool, "followers_count": int}` |

---

## 数据模型

```
User (Django auth)
 └── Profile (1:1)  ── display_name, role, avatar_char, avatar_color, bio,
                       post_count, follower_count, following_count,
                       essence_count, score

Board              ── name, slug, icon, en_name, description, sort_order,
                       post_count, today_count

Post               ── title, subtitle, excerpt, content (Markdown),
        ├── Board      author (User), board (Board), tags (M2M Tag),
        ├── User       is_essence, is_pinned, cover, cover_url,
        └── M2M Tag    view_count, like_count, comment_count, favorite_count

Comment            ── post (Post), author (User), parent (self, 一级嵌套),
                       content, like_count

Tag                ── name, count

Like               ── user, post, comment  (unique_together)

Favorite           ── user, post           (unique_together)

Follow             ── follower, following  (unique_together)

Notice             ── tag, content, link, is_active
```

---

## 自定义模板标签

在模板中加载：`{% load forum_extras %}`

| 标签 | 类型 | 用法 | 说明 |
|---|---|---|---|
| `markdown` | filter | `{{ post.content\|markdown }}` | 轻量 Markdown 渲染 |
| `time_ago` | filter | `{{ post.created_at\|time_ago }}` | 相对时间 |
| `excerpt_of` | filter | `{{ post\|excerpt_of:100 }}` | 生成摘要 |
| `url_replace` | tag | `{% url_replace request 'page' 2 %}` | 分页保留查询参数 |

---

## 管理命令

```bash
# 初始化演示数据（幂等，已存在则跳过）
python manage.py seed_data

# 强制清空并重写演示数据
python manage.py seed_data --force

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件（生产部署）
python manage.py collectstatic
```

---

## 生产部署

### 1. 配置生产环境

修改 `seeyou/settings.py`：

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 数据库切换为 PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'seeyou',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 静态文件
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### 2. 安装生产依赖

```bash
pip install gunicorn whitenoise psycopg2-binary
```

### 3. 部署步骤

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data
gunicorn seeyou.wsgi:application --bind 0.0.0.0:8000
```

### 4. 反向代理（Nginx 示例）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ { alias /path/to/staticfiles/; }
    location /media/  { alias /path/to/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 设计理念

> 山高水远，路在脚下。

本项目以《西游记》为精神底色，相信文字与影像的力量，相信每一段路都值得被记录。
设计上融合传统水墨美学与现代编辑式排版，以「墨韵西游」为视觉语言，
在朱砂红与古铜金之间，寻一条属于自己的取经路。

- **不堆砌功能**：每个功能都服务于「图文创作」这一核心
- **不依赖重型前端框架**：原生 HTML/CSS/JS，零构建步骤
- **不放弃美学追求**：水墨风不是装饰，是论坛的灵魂

---

## License

MIT License — 自由使用、修改、分发。

---

**取经路上，与君共话。**
