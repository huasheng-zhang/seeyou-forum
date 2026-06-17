"""boards/management/commands/seed_data.py — 初始化论坛数据

填充六洞天、用户、标签、帖子、评论、公告，让站点开箱可用。
用法：
    python manage.py seed_data            # 仅在空库时写入
    python manage.py seed_data --force    # 强制清空并重写
"""
import os
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Follow, Profile
from boards.models import (
    Board, Comment, Favorite, Like, Notice, Post, Tag,
)


# ============================================================
# 数据定义
# ============================================================

BOARDS = [
    {
        'name': '取经问道', 'icon': '问', 'en_name': 'scripture',
        'description': '研读经典，问道取经。此处谈《西游》文本、佛道思想、修行义理，以长文深度为主。',
        'sort_order': 1,
    },
    {
        'name': '花果山', 'icon': '果', 'en_name': 'flower-fruit',
        'description': '水帘洞内，闲话家常。生活、趣事、段子、日常，皆可入山。',
        'sort_order': 2,
    },
    {
        'name': '天宫广记', 'icon': '天', 'en_name': 'heavenly-annals',
        'description': '天庭广记，仙班轶事。神话、传说、神祇谱系、天宫制度考据。',
        'sort_order': 3,
    },
    {
        'name': '地府幽冥', 'icon': '幽', 'en_name': 'underworld',
        'description': '幽冥地府，生死之间。鬼神志怪、轮回观念、阴司文化。',
        'sort_order': 4,
    },
    {
        'name': '龙宫宝藏', 'icon': '龙', 'en_name': 'dragon-treasury',
        'description': '东海龙宫，宝藏奇珍。器物、兵器、法宝、神兵利器考。',
        'sort_order': 5,
    },
    {
        'name': '蓬莱仙岛', 'icon': '仙', 'en_name': 'penglai',
        'description': '蓬莱仙岛，以墨会友。原创水墨、插画、书法、影像作品展示。',
        'sort_order': 6,
    },
]

USERS = [
    {
        'username': 'moyike', 'display_name': '墨衣客',
        'email': 'moyike@seeyou.forum', 'password': 'seeyou12345',
        'role': '取经问道 · 主笔', 'avatar_char': '墨', 'avatar_color': 'dark',
        'bio': '古典文学研究者，长居长安。喜读《西游》，好作长文。相信文字是另一种金箍棒，可破心中贼。',
    },
    {
        'username': 'qingshandu', 'display_name': '青衫渡',
        'email': 'qingshandu@seeyou.forum', 'password': 'seeyou12345',
        'role': '蓬莱仙岛 · 画师', 'avatar_char': '青', 'avatar_color': 'jade',
        'bio': '水墨画师，画过火焰山、流沙河、五指山。相信真正的热，是克制里的灼人。',
    },
    {
        'username': 'youminglu', 'display_name': '幽冥录',
        'email': 'youminglu@seeyou.forum', 'password': 'seeyou12345',
        'role': '地府幽冥 · 长文', 'avatar_char': '幽', 'avatar_color': 'dark',
        'bio': '考据癖，专攻明清神魔小说。常驻地府版块，专治各种"细思极恐"。',
    },
    {
        'username': 'shangjianmingyue', 'display_name': '山间明月',
        'email': 'shangjianmingyue@seeyou.forum', 'password': 'seeyou12345',
        'role': '花果山 · 散客', 'avatar_char': '山', 'avatar_color': 'vermillion',
        'bio': '普通读者，喜欢在山间读《西游》。相信能在桌前坐定把话说完，也是一种反抗。',
    },
    {
        'username': 'zangjinge', 'display_name': '藏经阁主',
        'email': 'zangjinge@seeyou.forum', 'password': 'seeyou12345',
        'role': '取经问道 · 整理', 'avatar_char': '藏', 'avatar_color': 'gold',
        'bio': '藏经阁管理员，世德堂本与李评本对读爱好者。批语考据，乐此不疲。',
    },
]

TAGS = [
    '齐天大圣', '取经路', '水墨', '深度', '考据', '紧箍咒',
    '大闹天宫', '三打白骨精', '斗战胜佛', '火焰山', '心经', '金箍棒',
]

NOTICES = [
    {'tag': '活动', 'content': '壬寅年立秋 · 论坛第三百二十七期精华已收录', 'link': ''},
    {'tag': '版务', 'content': '花果山版块本周话题：你心中的齐天大圣', 'link': ''},
    {'tag': '招募', 'content': '蓬莱仙岛征稿：以墨写心，以文会友', 'link': ''},
    {'tag': '更新', 'content': '新功能上线：长文阅读模式 · 古风排版', 'link': ''},
]

# 帖子：标题、副标题、板块、作者、标签、精华、置顶、正文
POSTS = [
    {
        'title': '论孙悟空的反抗精神：从大闹天宫到西天成佛，他究竟妥协了什么？',
        'subtitle': 'On the Spirit of Rebellion — What Did Sun Wukong Truly Surrender?',
        'board': '取经问道', 'author': '墨衣客',
        'tags': ['齐天大圣', '深度', '紧箍咒', '大闹天宫', '斗战胜佛'],
        'is_essence': True, 'is_pinned': True,
        'excerpt': '五百年前，他打上凌霄宝殿；五百年后，他低头合掌。人们说这是驯化，可若细读文本，那根金箍棒从未真正放下——它只是从手中，移到了心里。',
        'content': '''五百年前，他打上凌霄宝殿，一根金箍棒搅得三界不宁；五百年后，他低头合掌，于灵山之上称臣受封。人们说这是成长，是驯化，是一个野性灵魂终于归顺了秩序。可若我们细读文本，会发现那根金箍棒从未真正放下——它只是从手中，移到了心里。

本文想谈的，不是孙悟空"是否反抗"，而是他反抗的形态，如何在十四年取经路上悄然转变。这种转变，或许比"反抗"本身更值得玩味。

## 一、大闹天宫：一场没有对象的战争

许多人将"大闹天宫"读作反抗权威的史诗，可若回到第七回之前，孙悟空的"反抗"其实缺乏明确的对象。他闹龙宫、闹地府、闹天庭，动机并非"不满天庭统治"，而是"我不服你这样待我"。他要的不是推翻秩序，而是秩序承认他的位置。

> 皇帝轮流做，明年到我家。
> ——第七回，孙悟空对如来语

这句话常被引为反抗宣言，可细究其逻辑，它恰恰暴露了孙悟空早期的局限：他反对的不是"皇帝"这个位置，而是"坐在皇帝位置上的不是我"。换言之，这是一种以自我为中心的、尚未触及秩序本质的反抗。他要的，是把自己也变成秩序的一部分。

正因如此，如来压他于五行山下，并非"镇压反抗"，而是给他五百年去想清楚一个问题：你究竟在反对什么？

◆ ◆ ◆

## 二、紧箍咒：反抗的内化

紧箍咒是《西游记》中最具隐喻色彩的器物。它不是物理的枷锁，而是一种"念诵即痛"的机制——这意味着，痛苦并非来自外力，而是来自"被提醒"。

唐僧念紧箍咒时，孙悟空头痛欲裂。可若我们留意，唐僧念的并非咒语本身，而是《心经》。换言之，让孙悟空痛苦的，不是某种神秘力量，而是"般若智慧"对一个躁动灵魂的反复敲打。

**紧箍不在头上，在心里。真正的反抗，是与自己和解。**

这是吴承恩极为精妙的一笔：反抗的形态，从"对外"转向了"对内"。孙悟空不再与天庭作战，他开始与自己作战——与那个躁动、好斗、不肯低头的自我作战。十四年取经路，本质上是一场漫长的内省。

### 三打白骨精：一次关键的转折

三打白骨精一节，常被读作"忠臣见疑"的悲剧，可若换一个视角，这恰是孙悟空反抗精神最纯粹的一次显现。他被逐回花果山，本可就此逍遥，可他终究回来了。这一次回来，不是因为紧箍，不是因为唐僧，而是因为他自己。

这是反抗的成熟：从"我必须反抗"到"我选择承担"。前者是本能，后者是自由。

## 三、成佛：反抗的最终形态

灵山之上，孙悟空被封为"斗战胜佛"。许多人读到这里感到失落，觉得英雄终被收编。可若我们回到"斗战"二字，会发现这个封号意味深长——他依然是"战"，依然是"胜"，只是战场变了。

> 我已成佛，与你一般，莫不去戴那箍儿了。
> ——第一百回，孙悟空语

他伸手摸头，金箍已自行消失。这意味着：当一个人不再需要被约束时，约束便不复存在。这不是妥协，这是超越。孙悟空没有放弃反抗，他放弃的，是那种"必须以对抗来证明自我"的执念。

所以，他究竟妥协了什么？

他妥协了"反抗的姿态"，却守住了"反抗的本质"。他不再需要打碎什么来证明自己，因为他已经知道，真正需要打碎的，从来不是外面的世界，而是心里那座五行山。

◆ ◆ ◆

## 余话：我们每个人的取经路

读《西游记》至最后一回，常有一种怅然。可若细想，这种怅然或许正是吴承恩想要的——他用一百万字告诉我们：真正的反抗，不是永远愤怒，而是知道为何而战，并愿意为此走完十万八千里。

我们每个人，都曾是那个大闹天宫的猴子。后来我们戴上了各自的紧箍，走入了各自的取经路。可只要心里那根金箍棒还在，我们就还没有真正妥协。

山高水远，路在脚下。''',
    },
    {
        'title': '火焰山意象：水墨如何画出"克制里的灼人"',
        'subtitle': 'Painting Fire with Restraint',
        'board': '蓬莱仙岛', 'author': '青衫渡',
        'tags': ['水墨', '火焰山', '深度'],
        'is_essence': True, 'is_pinned': False,
        'excerpt': '最初画火焰山时，我总想画得"烈"。后来才明白，真正的热，是克制里的灼人。本文记录这幅画从草稿到成画的三次推翻。',
        'content': '''最初画火焰山时，我总想画得"烈"。朱砂、赭石、藤黄，一层层往上堆，结果画面焦躁，像一团失控的火，反而失了"山"的体量。

第一次推翻：减色。把朱砂的比例从七成降到三成，加入大量淡墨做底。火从"主体"变成了"肌理"——山还是山，只是山在烧。

第二次推翻：留白。火焰山最热的不是火，是"将要烧起来"的瞬间。我在山腰留了一片空白，像一口未吐出的气。观者站在这片白前，会下意识屏住呼吸。

## 克制里的灼人

> 真正的热，不在火里，在观者的呼吸里。

第三次推翻：加印。在画面右下角盖了一方朱砂印，刻"灼"字。这是整幅画里唯一的纯红——其余的"火"都是墨与赭的混合。这方印，是火焰山的"眼"。

画完才悟：水墨画的不是物象，是"物象与观者之间的那口气"。墨衣客在《论孙悟空的反抗精神》里说"克制里的灼人，正是孙悟空成佛后的状态"——这话我画了三年才懂。

山高水远，墨在笔下。''',
    },
    {
        'title': '三打白骨精：被逐回花果山的那一夜，孙悟空在想什么？',
        'subtitle': 'The Night Wukong Was Sent Away',
        'board': '取经问道', 'author': '幽冥录',
        'tags': ['三打白骨精', '考据', '深度'],
        'is_essence': True, 'is_pinned': False,
        'excerpt': '世德堂本第二十七回，孙悟空被逐后回花果山，途中有一段极短的描写，常被读者忽略。可正是这段"留白"，藏着吴承恩最深的笔意。',
        'content': '''世德堂本第二十七回，孙悟空被逐后回花果山，途中有一段极短的描写，常被读者忽略。可正是这段"留白"，藏着吴承恩最深的笔意。

> 行者按下云头，寻思道："我若回花果山，又恐群猴笑我；若不回去，又无处安身。"

短短两句，写尽英雄的尴尬。他不是"被逐的忠臣"，他是"无处可去的猴子"。

## 考据：版本差异

李评本在此处加了批语："此猴尚有廉耻。"金圣叹则以为"未尽"，认为孙悟空所思不止"廉耻"，更有"自我"。

我倾向金圣叹。一个曾经大闹天宫的猴子，此刻担心的不是"群猴笑我"，而是"我何以至此"。这是反抗者第一次回望自己——回望那个曾经不需要任何人的自己。

## 那一夜

吴承恩没有写那一夜孙悟空做了什么。但我们可以推：他一定摸了摸头上的金箍。那个"摸"的动作，在第一百回金箍消失时再次出现——"摸了一摸，不见"。

> 这不是驯化，是共处。

被逐的那一夜，是孙悟空与金箍"共处"的开始。他不再咒骂它，他开始"摸"它。这是反抗的内化，也是自由的萌芽。''',
    },
    {
        'title': '今天在花果山读到一句话，想分享给大家',
        'subtitle': '',
        'board': '花果山', 'author': '山间明月',
        'tags': ['取经路'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '《西游》第八回，观音对孙悟空说："你须用心了。"读到这句，忽然眼眶一热。',
        'content': '''《西游》第八回，观音对孙悟空说："你须用心了。"

读到这句，忽然眼眶一热。

我们这代人，谁不是从大闹天宫走到西天成佛的呢。曾经以为反抗就是掀桌子，后来才知道，能在桌前坐定、把话说完，也是一种反抗。

山高水远，路在脚下。共勉。''',
    },
    {
        'title': '天宫制度考：玉帝凭什么管三界？',
        'subtitle': 'On the Legitimacy of the Jade Emperor',
        'board': '天宫广记', 'author': '藏经阁主',
        'tags': ['考据', '深度'],
        'is_essence': True, 'is_pinned': False,
        'excerpt': '玉帝的合法性来源，历来众说纷纭。本文从《西游》第七回如来的一段话切入，考据天宫制度的权力基础。',
        'content': '''玉帝的合法性来源，历来众说纷纭。本文从《西游》第七回如来的一段话切入，考据天宫制度的权力基础。

> 他自幼修持，苦历一千七百五十劫。每劫该十二万九千六百年。

如来这段话，常被读作"玉帝资历深"，可若细究，这是"合法性叙事"的典型构造——用"时间"换"正当性"。

## 时间的政治学

天宫的权力，不来自"武力"（孙悟空曾以此挑战），而来自"等待"。玉帝等了一千七百五十劫，这意味着：任何"快"的力量，都无法撼动"慢"的秩序。

> 这是天宫最深的设计：让反抗者等不起。

## 与人间的对应

明代官僚制度，恰是这种"慢"的镜像。一个寒门子弟，从秀才到内阁，平均需要四十年。玉帝的一千七百五十劫，是这个"四十年"的神圣化投射。

吴承恩写天宫，写的是人间。''',
    },
    {
        'title': '金箍棒考：一万三千五百斤，这个数字有何玄机？',
        'subtitle': 'The Weight of 13,500 Jin',
        'board': '龙宫宝藏', 'author': '藏经阁主',
        'tags': ['金箍棒', '考据'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '金箍棒重一万三千五百斤。这个数字并非随意，而是暗合《黄帝内经》"人一日一夜呼吸一万三千五百息"。',
        'content': '''金箍棒重一万三千五百斤。这个数字并非随意，而是暗合《黄帝内经》"人一日一夜呼吸一万三千五百息"。

这意味着：金箍棒 = 人的呼吸。

## 呼吸与反抗

呼吸是人最本能的"反抗"——只要还在呼吸，就还在与世界博弈。孙悟空的金箍棒，本质上是他的"呼吸"。

> 所以，当金箍棒从手中移到心里，不是消失，是"内化为呼吸"。

这也是为什么，成佛后金箍棒不再出现——因为它已经成了孙悟空的呼吸本身。一个呼吸即反抗的人，不需要再"挥棒"。

## 龙宫取宝的隐喻

龙王说"这棒无人能使"，可孙悟空一拿便使。这不是"缘分"，而是"呼吸认呼吸"——金箍棒在等一个真正"会呼吸"的人。

山高水远，呼吸在身。''',
    },
    {
        'title': '地府生死簿：孙悟空划名，究竟划掉了什么？',
        'subtitle': 'What Did Wukong Erase from the Book of Life and Death?',
        'board': '地府幽冥', 'author': '幽冥录',
        'tags': ['考据', '大闹天宫'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '第三回，孙悟空在生死簿上划掉了猴属之名。常被读作"反抗死亡"，可若细究，他划掉的是"被定义"。',
        'content': '''第三回，孙悟空在生死簿上划掉了猴属之名。常被读作"反抗死亡"，可若细究，他划掉的是"被定义"。

生死簿的本质，不是"记录生死"，而是"定义你是谁"。孙悟空划名，不是要"不死"，而是要"不被定义"。

## 划名之后

划名之后，孙悟空并未真正"不死"——他在第六回被如来压五行山，本质是一种"死"。但他"不被定义"了：他不再是"猴属"，他是"齐天大圣"。

> 反抗死亡是徒劳的，反抗定义才是反抗。

## 与紧箍的对照

生死簿是"被定义"，紧箍是"被约束"。前者划掉，后者内化。孙悟空的反抗史，是一部从"拒绝被定义"到"主动选择约束"的进化史。

这是真正的成熟。''',
    },
    {
        'title': '《心经》与紧箍咒：唐僧念的到底是什么？',
        'subtitle': 'The Heart Sutra as the Tightening Spell',
        'board': '取经问道', 'author': '墨衣客',
        'tags': ['心经', '紧箍咒', '深度'],
        'is_essence': True, 'is_pinned': False,
        'excerpt': '《西游》第十九回，乌巢禅师传唐僧《心经》。此后唐僧念紧箍咒，所念实为《心经》。这是吴承恩最深的隐喻。',
        'content': '''《西游》第十九回，乌巢禅师传唐僧《心经》。此后唐僧念紧箍咒，所念实为《心经》。这是吴承恩最深的隐喻。

## 《心经》是什么

《般若波罗蜜多心经》，二百六十字，讲"色即是空，空即是色"。它是大乘佛教"般若"思想的浓缩——般若，即"智慧"。

> 让孙悟空痛苦的，不是咒语，是智慧。

## 智慧即痛苦

一个躁动的灵魂，被智慧反复敲打，必然痛苦。这种痛苦不是惩罚，是"觉醒的阵痛"。紧箍咒的"痛"，本质是"看见自己"的痛。

## 内化的过程

第十四回，孙悟空初戴紧箍，痛得打滚。第一百回，金箍自去，他不痛了。这中间的九十一回，是他从"被智慧敲打"到"与智慧共处"的过程。

> 紧箍不在头上，在心里。

当智慧成为呼吸，紧箍便不再需要。这是《西游》最深的一笔。''',
    },
    {
        'title': '画了一幅《斗战胜佛》，献给墨衣客',
        'subtitle': 'A Painting for the Victorious Buddha',
        'board': '蓬莱仙岛', 'author': '青衫渡',
        'tags': ['水墨', '斗战胜佛'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '墨衣客说"期待你下一幅《斗战胜佛》"。画了三个月，今天终于成画。不画他合掌，画他"摸头"的那一瞬。',
        'content': '''墨衣客说"期待你下一幅《斗战胜佛》"。画了三个月，今天终于成画。

不画他合掌，画他"摸头"的那一瞬。

## 为什么画"摸头"

第一百回，孙悟空成佛后，第一反应不是得意，而是"摸了一摸，不见"。这个"摸"字极妙——他不是"看见"金箍没了，而是"确认"它没了。

> 这说明这十四年，他始终知道它在。这不是驯化，是共处。

画"摸头"，就是画"共处"。画一个曾经反抗的人，与自己的紧箍和解的瞬间。

## 画面

整幅画只画一只手，摸向一个光头。手是墨，头是留白。没有金箍——因为金箍已经不在了。但手的姿态，是"确认它在不在"的姿态。

这是整幅画的"眼"：金箍不在了，但"摸"还在。

山高水远，墨在笔下。''',
    },
    {
        'title': '新手报到：刚加入西游论坛，想问个问题',
        'subtitle': '',
        'board': '花果山', 'author': '山间明月',
        'tags': ['取经路'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '大家好，我是山间明月。读《西游》三年，第一次找到同好。想问大家：你们最喜欢哪一回？',
        'content': '''大家好，我是山间明月。读《西游》三年，第一次找到同好。

想问大家：你们最喜欢哪一回？

我最喜欢第二十七回，三打白骨精。孙悟空被逐的那一夜，我读一次哭一次。

期待大家的回答。山高水远，路在脚下。''',
    },
    {
        'title': '天宫宴饮考：蟠桃会的座次藏着什么玄机？',
        'subtitle': 'The Seating of the Peach Banquet',
        'board': '天宫广记', 'author': '藏经阁主',
        'tags': ['考据', '大闹天宫'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '蟠桃会的座次，常被读作"神仙排位"。可若细究，这是一份"权力拓扑图"——谁坐哪里，决定了孙悟空为何"闹"。',
        'content': '''蟠桃会的座次，常被读作"神仙排位"。可若细究，这是一份"权力拓扑图"——谁坐哪里，决定了孙悟空为何"闹"。

## 座次分析

据第五回，蟠桃会邀请名单：西天佛老、菩萨、罗汉、玉帝、王母、上八洞神仙、下八洞神仙……独独没有"齐天大圣"。

> 孙悟空的"闹"，不是没被邀请，是"有名无位"。

## 有名无位的痛苦

"齐天大圣"是玉帝封的，意味着"名"被承认。但蟠桃会没有他的座次，意味着"位"被否认。

名位分离，是明代官场的典型困境——一个"挂衔"的官员，没有实权。孙悟空的痛苦，是明代所有"挂衔者"的痛苦。

## 闹的真相

所以"大闹天宫"不是反抗权威，是"讨位"。他要的不是推翻天宫，是天宫给他一个"实位"。

> 这是反抗的早期形态：以自我为中心，尚未触及秩序本质。

直到五行山下五百年，他才想清楚这个问题。''',
    },
    {
        'title': '龙宫取宝：定海神针为何"认"孙悟空？',
        'subtitle': 'Why the Pillar Chose Wukong',
        'board': '龙宫宝藏', 'author': '幽冥录',
        'tags': ['金箍棒', '考据'],
        'is_essence': False, 'is_pinned': False,
        'excerpt': '定海神针"霞光艳艳"，孙悟空一到便"认主"。这不是缘分，是"呼吸认呼吸"——金箍棒在等一个真正"会呼吸"的人。',
        'content': '''定海神针"霞光艳艳"，孙悟空一到便"认主"。这不是缘分，是"呼吸认呼吸"——金箍棒在等一个真正"会呼吸"的人。

## 定海神针的本职

定海神针，本是"定海"的——它是一根"测量海深"的柱子，不是兵器。龙王说"无用"，是因为它"不是兵器"。

> 但孙悟空拿起来，它就成了兵器。

## 用的转换

一根"测量"的柱子，被孙悟空变成了"挥舞"的棒。这是"用"的转换——从"被动测量"到"主动挥舞"。

这也是反抗的本质：把"被定义的工具"变成"自我表达的方式"。金箍棒在龙王手里是"测量"，在孙悟空手里是"反抗"。

## 呼吸认呼吸

金箍棒重一万三千五百斤，暗合人一日呼吸之数。所以它"认"孙悟空——因为孙悟空是当时三界唯一"会呼吸"的人。

> 其他神仙都在"等"，只有孙悟空在"呼吸"。

山高水远，呼吸在身。''',
    },
]

# 评论：帖子序号、作者、内容、父评论序号（可选）
COMMENTS = [
    {'post': 0, 'author': '青衫渡', 'parent': None,
     'content': '"反抗的姿态"与"反抗的本质"这一组区分太精准了。忽然想起自己画火焰山时的心境——最初总想画得"烈"，后来才明白，真正的热，是克制里的灼人。墨衣客此文，与我画中所悟，竟是一理。'},
    {'post': 0, 'author': '墨衣客', 'parent': 0,
     'content': '青衫兄所言极是。所谓"克制里的灼人"，正是孙悟空成佛后的状态——他不再需要燃烧来证明火的存在。期待你下一幅《斗战胜佛》。'},
    {'post': 0, 'author': '幽冥录', 'parent': None,
     'content': '补充一个细节：原著中孙悟空摸头发现金箍消失后，第一反应不是得意，而是"摸了一摸，不见"。这个"摸"字极妙——他不是"看见"金箍没了，而是"确认"它没了。说明这十四年，他始终知道它在。这不是驯化，是共处。'},
    {'post': 0, 'author': '山间明月', 'parent': None,
     'content': '读完想哭。我们这代人，谁不是从大闹天宫走到西天成佛的呢。曾经以为反抗就是掀桌子，后来才知道，能在桌前坐定、把话说完，也是一种反抗。'},
    {'post': 0, 'author': '藏经阁主', 'parent': None,
     'content': '从文本考据角度补充：世德堂本与李评本在此处的批语差异颇大。李卓吾批"金箍自去"四字曰"妙"，而金圣叹则以为"未尽"。可见明清两代读者对此处的理解，本就两途。墨衣客此文，更近李评一路。'},
    {'post': 1, 'author': '墨衣客', 'parent': None,
     'content': '青衫兄此画论，与我的文论竟是一理。"克制里的灼人"——这话我借去用进下一篇文章了。'},
    {'post': 2, 'author': '墨衣客', 'parent': None,
     'content': '幽冥兄考据精到。"摸"字之妙，我写文时未及展开，兄补得正是地方。'},
    {'post': 4, 'author': '墨衣客', 'parent': None,
     'content': '藏经阁主此考，把"时间政治学"讲透了。玉帝的一千七百五十劫，确实是明代官僚"慢"的神圣化。受教。'},
    {'post': 7, 'author': '青衫渡', 'parent': None,
     'content': '墨衣客说"期待你下一幅《斗战胜佛》"。我画了三个月，明天就发出来，献给墨衣客。'},
]


# ============================================================
# 命令
# ============================================================

class Command(BaseCommand):
    help = '初始化论坛数据：六洞天、用户、标签、帖子、评论、公告'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='强制清空并重写（会删除现有数据）',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)

        if force:
            self.stdout.write(self.style.WARNING('清空现有数据…'))
            Comment.objects.all().delete()
            Like.objects.all().delete()
            Favorite.objects.all().delete()
            Follow.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Notice.objects.all().delete()
            Board.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # 幂等检查
        if Board.objects.exists() and not force:
            self.stdout.write(self.style.SUCCESS('数据已存在，跳过。如需重写请加 --force'))
            return

        self.stdout.write('创建板块…')
        boards = {}
        for b in BOARDS:
            boards[b['name']] = Board.objects.create(
                name=b['name'], icon=b['icon'], en_name=b['en_name'],
                description=b['description'], sort_order=b['sort_order'],
            )

        self.stdout.write('创建用户…')
        users = {}
        for u in USERS:
            user = User.objects.create_user(
                username=u['username'], email=u['email'],
                password=u['password'],
            )
            Profile.objects.create(
                user=user, display_name=u['display_name'],
                role=u['role'], avatar_char=u['avatar_char'],
                avatar_color=u['avatar_color'], bio=u['bio'],
            )
            users[u['display_name']] = user

        self.stdout.write('创建标签…')
        tags = {}
        for t in TAGS:
            tags[t] = Tag.objects.create(name=t, count=0)

        self.stdout.write('创建公告…')
        for n in NOTICES:
            Notice.objects.create(
                tag=n['tag'], content=n['content'],
                link=n.get('link', ''), is_active=True,
            )

        self.stdout.write('创建帖子…')
        posts = []
        for idx, p in enumerate(POSTS):
            post = Post.objects.create(
                title=p['title'], subtitle=p.get('subtitle', ''),
                excerpt=p.get('excerpt', ''), content=p['content'],
                author=users[p['author']], board=boards[p['board']],
                is_essence=p.get('is_essence', False),
                is_pinned=p.get('is_pinned', False),
                cover_url=(
                    'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image'
                    '?prompt=' + (
                        'Chinese%20ink%20wash%20painting%20'
                        + p['board'].replace(' ', '%20')
                        + '%20sumi-e%20vermillion%20seal%20minimal%20'
                        'mountain%20mist%20epic'
                    ) + '&image_size=landscape_16_9'
                ),
                view_count=random.randint(800, 9000),
                like_count=random.randint(50, 1200),
                comment_count=0,
                favorite_count=random.randint(20, 400),
            )
            for tname in p.get('tags', []):
                if tname in tags:
                    post.tags.add(tags[tname])
                    tags[tname].count += 1
                    tags[tname].save()
            posts.append(post)
            # 更新作者与板块计数
            prof = users[p['author']].profile
            prof.post_count += 1
            prof.score += 10
            if p.get('is_essence'):
                prof.essence_count += 1
                prof.score += 50
            prof.save()
            b = boards[p['board']]
            b.post_count += 1
            b.today_count += 1
            b.save()

        self.stdout.write('创建评论…')
        for c in COMMENTS:
            post = posts[c['post']]
            parent = None
            if c.get('parent') is not None:
                # 找到该帖的第 N 条评论（按创建顺序）
                existing = list(post.comments.order_by('created_at'))
                if c['parent'] < len(existing):
                    parent = existing[c['parent']]
            comment = Comment.objects.create(
                post=post, author=users[c['author']],
                parent=parent, content=c['content'],
                like_count=random.randint(10, 200),
            )
            post.comment_count += 1
            post.save()

        self.stdout.write('建立关注关系…')
        # 墨衣客 关注 青衫渡、幽冥录
        Follow.objects.create(follower=users['墨衣客'], following=users['青衫渡'])
        Follow.objects.create(follower=users['墨衣客'], following=users['幽冥录'])
        # 青衫渡 关注 墨衣客
        Follow.objects.create(follower=users['青衫渡'], following=users['墨衣客'])
        # 山间明月 关注 墨衣客、青衫渡、幽冥录、藏经阁主
        for target in ['墨衣客', '青衫渡', '幽冥录', '藏经阁主']:
            Follow.objects.create(follower=users['山间明月'], following=users[target])
        # 藏经阁主 关注 墨衣客
        Follow.objects.create(follower=users['藏经阁主'], following=users['墨衣客'])
        # 幽冥录 关注 墨衣客、藏经阁主
        Follow.objects.create(follower=users['幽冥录'], following=users['墨衣客'])
        Follow.objects.create(follower=users['幽冥录'], following=users['藏经阁主'])

        # 更新关注计数
        follow_map = {
            '墨衣客': (4, 2),  # 粉丝 4，关注 2
            '青衫渡': (1, 1),
            '幽冥录': (2, 2),
            '山间明月': (0, 4),
            '藏经阁主': (2, 1),
        }
        for name, (followers, following) in follow_map.items():
            p = users[name].profile
            p.follower_count = followers
            p.following_count = following
            p.save()

        self.stdout.write('创建收藏…')
        # 山间明月 收藏前 3 篇精华
        for i in range(3):
            Favorite.objects.create(user=users['山间明月'], post=posts[i])
            posts[i].favorite_count += 1
            posts[i].save()
        # 青衫渡 收藏第 1 篇
        Favorite.objects.create(user=users['青衫渡'], post=posts[0])

        self.stdout.write(self.style.SUCCESS(
            f'\n初始化完成！\n'
            f'  板块：{Board.objects.count()}\n'
            f'  用户：{User.objects.count() - 1}（不含 admin）\n'
            f'  标签：{Tag.objects.count()}\n'
            f'  帖子：{Post.objects.count()}\n'
            f'  评论：{Comment.objects.count()}\n'
            f'  公告：{Notice.objects.count()}\n'
            f'  关注：{Follow.objects.count()}\n'
            f'  收藏：{Favorite.objects.count()}\n\n'
            f'测试账号（密码均为 seeyou12345）：\n'
            f'  moyike / qingshandu / youminglu / shangjianmingyue / zangjinge\n'
        ))
