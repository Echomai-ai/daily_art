# -*- coding: utf-8 -*-
"""每日天气诗意卡片生成器
ponytail: 单文件零依赖，离线兜底覆盖所有场景。
依赖: Python标准库 (json, urllib, random, datetime)
"""

import json
import os
import urllib.request
import urllib.error
import random
from datetime import date, datetime

# ============================================================
# 节气计算 - 基于立春日 + 约15.22天间隔的近似算法
# ponytail: 误差±1天内，对每日卡片场景足够
# 升级路径: 需要精确到时刻时可换用 PyMeeus/ephem 库
# ============================================================
SOLAR_TERMS = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

# 各年立春日期 (月, 日)，用于节气计算锚点
LICHUN_DATES = {2025: (2, 3), 2026: (2, 4), 2027: (2, 4), 2028: (2, 4)}


def f_get_solar_term(v_date):
    """根据日期返回对应节气"""
    v_year = v_date.year
    v_lichun = LICHUN_DATES.get(v_year, LICHUN_DATES.get(2026, (2, 4)))
    v_lichun_date = date(v_year, v_lichun[0], v_lichun[1])
    v_delta = (v_date - v_lichun_date).days
    if v_delta < 0:
        # 当前日期在立春之前，属于上一年的大寒周期
        v_prev_year = v_year - 1
        v_prev_lichun = LICHUN_DATES.get(v_prev_year, (2, 4))
        v_prev_lichun_date = date(v_prev_year, v_prev_lichun[0], v_prev_lichun[1])
        v_delta = (v_date - v_prev_lichun_date).days
    v_index = int(v_delta / 15.22) % 24
    return SOLAR_TERMS[v_index]


def f_get_season(v_term):
    """根据节气返回季节"""
    if v_term in ("立春", "雨水", "惊蛰", "春分", "清明", "谷雨"):
        return "春"
    elif v_term in ("立夏", "小满", "芒种", "夏至", "小暑", "大暑"):
        return "夏"
    elif v_term in ("立秋", "处暑", "白露", "秋分", "寒露", "霜降"):
        return "秋"
    else:
        return "冬"


# ============================================================
# 天气获取 - wttr.in 免费API，无需密钥
# ponytail: 网络不可用时返回空，前端展示占位信息
# ============================================================
def f_get_weather(v_city="Wuhan"):
    """从 wttr.in 获取天气，失败返回 None"""
    try:
        v_url = f"https://wttr.in/{v_city}?format=j1&lang=zh"
        v_req = urllib.request.Request(v_url, headers={"User-Agent": "curl/7.0"})
        with urllib.request.urlopen(v_req, timeout=10) as v_resp:
            v_data = json.loads(v_resp.read().decode("utf-8"))
        v_cur = v_data["current_condition"][0]
        # 今日预报
        v_forecast = v_data["weather"][0]
        return {
            "city": "武汉",
            "temp": f"{v_cur['temp_C']}°C",
            "desc": v_cur["weatherDesc"][0]["value"],
            "humidity": f"{v_cur['humidity']}%",
            "wind": f"{v_cur['windspeedKmph']} km/h",
            "high": f"{v_forecast['maxtempC']}°C",
            "low": f"{v_forecast['mintempC']}°C",
        }
    except Exception:
        return None


# ============================================================
# 诗句 - 按季节+天气精选古诗，离网兜底
# ponytail: 共约50句，覆盖四季+晴雨雪风等天气
# ============================================================
POEMS = {
    # 春季
    ("春", "晴"): [
        ("春眠不觉晓，处处闻啼鸟。", "孟浩然《春晓》"),
        ("等闲识得东风面，万紫千红总是春。", "朱熹《春日》"),
        ("迟日江山丽，春风花草香。", "杜甫《绝句》"),
        ("日出江花红胜火，春来江水绿如蓝。", "白居易《忆江南》"),
    ],
    ("春", "雨"): [
        ("好雨知时节，当春乃发生。", "杜甫《春夜喜雨》"),
        ("天街小雨润如酥，草色遥看近却无。", "韩愈《早春呈水部张十八员外》"),
        ("小楼一夜听春雨，深巷明朝卖杏花。", "陆游《临安春雨初霁》"),
    ],
    ("春", "云"): [
        ("云想衣裳花想容，春风拂槛露华浓。", "李白《清平调》"),
        ("春江潮水连海平，海上明月共潮生。", "张若虚《春江花月夜》"),
    ],
    # 夏季
    ("夏", "晴"): [
        ("接天莲叶无穷碧，映日荷花别样红。", "杨万里《晓出净慈寺送林子方》"),
        ("绿树阴浓夏日长，楼台倒影入池塘。", "高骈《山亭夏日》"),
        ("纷纷红紫已成尘，布谷声中夏令新。", "陆游《初夏绝句》"),
    ],
    ("夏", "雨"): [
        ("黑云翻墨未遮山，白雨跳珠乱入船。", "苏轼《六月二十七日望湖楼醉书》"),
        ("黄梅时节家家雨，青草池塘处处蛙。", "赵师秀《约客》"),
        ("七八个星天外，两三点雨山前。", "辛弃疾《西江月》"),
    ],
    # 秋季
    ("秋", "晴"): [
        ("晴空一鹤排云上，便引诗情到碧霄。", "刘禹锡《秋词》"),
        ("停车坐爱枫林晚，霜叶红于二月花。", "杜牧《山行》"),
        ("自古逢秋悲寂寥，我言秋日胜春朝。", "刘禹锡《秋词》"),
        ("落霞与孤鹜齐飞，秋水共长天一色。", "王勃《滕王阁序》"),
    ],
    ("秋", "雨"): [
        ("空山新雨后，天气晚来秋。", "王维《山居秋暝》"),
        ("君问归期未有期，巴山夜雨涨秋池。", "李商隐《夜雨寄北》"),
        ("秋风秋雨愁煞人。", "秋瑾（引清·陶澹人句）"),
    ],
    ("秋", "风"): [
        ("长风万里送秋雁，对此可以酣高楼。", "李白《宣州谢朓楼饯别校书叔云》"),
        ("秋风起兮白云飞，草木黄落兮雁南归。", "刘彻《秋风辞》"),
    ],
    # 冬季
    ("冬", "晴"): [
        ("忽如一夜春风来，千树万树梨花开。", "岑参《白雪歌送武判官归京》"),
        ("千山鸟飞绝，万径人踪灭。", "柳宗元《江雪》"),
        ("墙角数枝梅，凌寒独自开。", "王安石《梅花》"),
    ],
    ("冬", "雨"): [
        ("寒雨连江夜入吴，平明送客楚山孤。", "王昌龄《芙蓉楼送辛渐》"),
    ],
    ("冬", "雪"): [
        ("忽如一夜春风来，千树万树梨花开。", "岑参《白雪歌送武判官归京》"),
        ("晚来天欲雪，能饮一杯无？", "白居易《问刘十九》"),
        ("孤舟蓑笠翁，独钓寒江雪。", "柳宗元《江雪》"),
        ("梅须逊雪三分白，雪却输梅一段香。", "卢梅坡《雪梅》"),
    ],
    ("冬", "风"): [
        ("北风卷地白草折，胡天八月即飞雪。", "岑参《白雪歌送武判官归京》"),
        ("寒风摧树木，严霜结庭兰。", "汉乐府《孔雀东南飞》"),
    ],
}

# 通用兜底诗句（跨季节）
FALLBACK_POEMS = [
    ("人生若只如初见，何事秋风悲画扇。", "纳兰性德《木兰花令》"),
    ("此情可待成追忆，只是当时已惘然。", "李商隐《锦瑟》"),
    ("衣带渐宽终不悔，为伊消得人憔悴。", "柳永《蝶恋花》"),
    ("纸上得来终觉浅，绝知此事要躬行。", "陆游《冬夜读书示子聿》"),
    ("问渠那得清如许，为有源头活水来。", "朱熹《观书有感》"),
    ("大漠孤烟直，长河落日圆。", "王维《使至塞上》"),
    ("明月几时有，把酒问青天。", "苏轼《水调歌头》"),
    ("但愿人长久，千里共婵娟。", "苏轼《水调歌头》"),
]


def f_get_weather_key(v_weather_desc):
    """从天气描述提取关键词，支持中英文"""
    v_desc = v_weather_desc or ""
    v_desc_lower = v_desc.lower()
    for v_kw in ["雪", "雨", "风", "雾", "云", "阴"]:
        if v_kw in v_desc:
            return v_kw
    for v_en, v_cn in [("snow", "雪"), ("rain", "雨"), ("drizzle", "雨"),
                        ("shower", "雨"), ("thunder", "雨"),
                        ("wind", "风"), ("fog", "雾"), ("mist", "雾"),
                        ("haze", "雾"), ("cloud", "云"), ("overcast", "阴"),
                        ("sunny", "晴"), ("clear", "晴")]:
        if v_en in v_desc_lower:
            return v_cn
    return "晴"


def f_get_poem(v_season, v_weather_desc=""):
    """根据季节和天气描述匹配诗句，未匹配则随机选通用句"""
    v_season = v_season or "春"
    v_weather_key = f_get_weather_key(v_weather_desc)
    # 尝试匹配
    for v_key in [(v_season, v_weather_key), (v_season, "晴")]:
        if v_key in POEMS and POEMS[v_key]:
            return random.choice(POEMS[v_key])
    # 兜底
    return random.choice(FALLBACK_POEMS)


# ============================================================
# AI 句子生成 - 调用硅基流动免费API (可选)
# ponytail: API不可用时用预设诗意句子兜底
# ============================================================
def f_generate_sentence(v_weather_dict, v_term):
    """尝试用AI生成一句话，失败返回 None"""
    try:
        v_api_key = "sk-your-api-key-here"  # 用户替换为自己的API Key
        if "your-api-key" in v_api_key:
            return None  # 未配置则跳过
        v_weather_text = ""
        if v_weather_dict:
            v_weather_text = f"天气{v_weather_dict.get('desc','')}，气温{v_weather_dict.get('temp','')}"
        v_prompt = (
            f"今天是{v_term}节气，{v_weather_text}。"
            f"请用一句话（20字以内）描绘今日武汉的意境，要有诗意和温度感。"
            f"只输出句子，不要引号不要解释。"
        )
        v_body = json.dumps({
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": v_prompt}],
            "max_tokens": 60,
        }).encode("utf-8")
        v_req = urllib.request.Request(
            "https://api.siliconflow.cn/v1/chat/completions",
            data=v_body,
            headers={
                "Authorization": f"Bearer {v_api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(v_req, timeout=15) as v_resp:
            v_result = json.loads(v_resp.read().decode("utf-8"))
        return v_result["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    except Exception:
        return None


# AI 生成失败时的兜底句子（按节气定制）
FALLBACK_SENTENCES = {
    "立春": "东风解冻，万物始生，武汉的春天从今日醒来。",
    "雨水": "细雨润江城，草木萌动，空气中都是生长的味道。",
    "惊蛰": "春雷乍动，惊醒了东湖边沉睡的虫儿与花苞。",
    "春分": "昼夜平分春色，珞珈山的樱花正酝酿一场盛放。",
    "清明": "天清地明，江城的柳絮轻扬，怀念与希望同在。",
    "谷雨": "雨生百谷，汉阳树下的新绿，是春天最后的告白。",
    "立夏": "蝉声未起，暑气初临，武汉的夏天已悄悄抵达。",
    "小满": "麦穗初满，江风微热，日子不疾不徐刚刚好。",
    "芒种": "忙种忙收，长江边的梅雨季，空气黏黏的都是诗意。",
    "夏至": "白日最长，东湖的荷花在烈日下开得不管不顾。",
    "小暑": "温风至，蟋蟀居宇，武汉的热才刚刚开始。",
    "大暑": "三伏正中，江城的每一阵风都是热的，冰西瓜最甜。",
    "立秋": "梧桐一叶落，天下尽知秋，武汉的秋天从今天开始。",
    "处暑": "暑气渐消，江边的晚风终于有了丝丝凉意。",
    "白露": "露从今夜白，黄鹤楼头的月色格外清亮。",
    "秋分": "昼夜均而寒暑平，桂花香满了整座江城。",
    "寒露": "露水渐寒，长江上的雾气开始浓重起来。",
    "霜降": "草木黄落，武汉的深秋，天高云淡最宜登楼。",
    "立冬": "水始冰，地始冻，武汉的冬天从一碗藕汤开始。",
    "小雪": "虹藏不见，天气上升，江城的冬日阳光格外珍贵。",
    "大雪": "至此而雪盛，虽未必有雪，寒意已深入骨髓。",
    "冬至": "日短之至，阳气始生，武汉人该吃饺子了。",
    "小寒": "冷在三九，东湖的风像刀子，但梅花开得正好。",
    "大寒": "寒气逆极，春归有期，最冷的时候也是最近的春天。",
}


# ============================================================
# 图片获取 - Pexels API 优先，Wikimedia 名画兜底
# ponytail: 都不行时 HTML 端有 CSS 渐变兜底
# 获取 Key: https://www.pexels.com/api/  即时生效，无需审核
# ============================================================
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# 季节+天气 → Pexels 搜索关键词
SEASON_WEATHER_QUERIES = {
    ("春", "晴"): "spring blossom nature sunny",
    ("春", "雨"): "spring rain flower",
    ("春", "风"): "spring wind cherry blossom",
    ("夏", "晴"): "summer nature sunny lake",
    ("夏", "雨"): "summer rain lotus",
    ("夏", "风"): "summer breeze ocean",
    ("秋", "晴"): "autumn forest golden sunlight",
    ("秋", "雨"): "autumn rain mist",
    ("秋", "风"): "autumn wind leaves",
    ("冬", "晴"): "winter snow sunlight mountain",
    ("冬", "雪"): "winter snow landscape",
    ("冬", "风"): "winter wind snow",
    ("冬", "雨"): "winter rain mist",
}


def f_get_pexels_image(v_season, v_weather_key):
    """从 Pexels 获取图片，失败返回 None"""
    if not PEXELS_API_KEY:
        print("  [Pexels] 未配置 API Key")
        return None
    v_query = SEASON_WEATHER_QUERIES.get(
        (v_season, v_weather_key),
        SEASON_WEATHER_QUERIES.get((v_season, "晴"), "nature landscape"),
    )
    try:
        v_url = (
            f"https://api.pexels.com/v1/search"
            f"?query={v_query}&orientation=landscape&per_page=1"
        )
        v_req = urllib.request.Request(
            v_url, headers={"Authorization": PEXELS_API_KEY}
        )
        with urllib.request.urlopen(v_req, timeout=10) as v_resp:
            v_data = json.loads(v_resp.read().decode("utf-8"))
        v_photos = v_data.get("photos", [])
        if v_photos:
            print(f"  [Pexels] 获取成功: {v_query}")
            return v_photos[0]["src"]["large"]
        print(f"  [Pexels] 无结果: {v_query}")
        return None
    except Exception as v_e:
        print(f"  [Pexels] 失败: {v_e}")
        return None


# 世界名画兜底（公共领域，Wikimedia Commons）
IMAGE_URLS = {
    ("春", "晴"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Claude_Monet_-_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son_-_Google_Art_Project.jpg/800px-Claude_Monet_-_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son_-_Google_Art_Project.jpg",
    ],
    ("春", "雨"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Gustave_Caillebotte_-_Paris_Street%3B_Rainy_Day_-_Google_Art_Project.jpg/1280px-Gustave_Caillebotte_-_Paris_Street%3B_Rainy_Day_-_Google_Art_Project.jpg",
    ],
    ("夏", "晴"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Claude_Monet_-_The_Water_Lily_Pond_%28Bridge_over_the_Water-Lily_Pond%29.jpg/1280px-Claude_Monet_-_The_Water_Lily_Pond_%28Bridge_over_the_Water-Lily_Pond%29.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Claude_Monet_-_Woman_in_the_Garden.jpg/800px-Claude_Monet_-_Woman_in_the_Garden.jpg",
    ],
    ("夏", "雨"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Hiroshige_II_-_Sudden_Shower_over_Shin-Ohashi_Bridge_and_Atake.jpg/800px-Hiroshige_II_-_Sudden_Shower_over_Shin-Ohashi_Bridge_and_Atake.jpg",
    ],
    ("秋", "晴"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Vincent_van_Gogh_-_Alley_in_Autumn_%28F1700%29.jpg/800px-Vincent_van_Gogh_-_Alley_in_Autumn_%28F1700%29.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/John_Everett_Millais_-_Autumn_Leaves_-_Google_Art_Project.jpg/800px-John_Everett_Millais_-_Autumn_Leaves_-_Google_Art_Project.jpg",
    ],
    ("秋", "风"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/800px-Tsunami_by_hokusai_19th_century.jpg",
    ],
    ("冬", "晴"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg/1280px-Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Pieter_Bruegel_the_Elder_-_Hunters_in_the_Snow_%28Winter%29_-_Google_Art_Project.jpg/1280px-Pieter_Bruegel_the_Elder_-_Hunters_in_the_Snow_%28Winter%29_-_Google_Art_Project.jpg",
    ],
    ("冬", "雪"): [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg/1280px-Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Pieter_Bruegel_the_Elder_-_Hunters_in_the_Snow_%28Winter%29_-_Google_Art_Project.jpg/1280px-Pieter_Bruegel_the_Elder_-_Hunters_in_the_Snow_%28Winter%29_-_Google_Art_Project.jpg",
    ],
}

# 通用名画兜底（当季天气匹配不到时随机选）
FALLBACK_IMAGES = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Claude_Monet_-_The_Water_Lily_Pond_%28Bridge_over_the_Water-Lily_Pond%29.jpg/1280px-Claude_Monet_-_The_Water_Lily_Pond_%28Bridge_over_the_Water-Lily_Pond%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Vincent_van_Gogh_-_Wheat_Field_with_Cypresses_-_Google_Art_Project.jpg/800px-Vincent_van_Gogh_-_Wheat_Field_with_Cypresses_-_Google_Art_Project.jpg",
]


def f_get_image(v_season, v_weather_desc=""):
    """Pexels 优先 → 名画兜底 → HTML 渐变托底
    返回 (url, source) 元组，source 为 'pexels' / 'wikimedia' / 'fallback'
    """
    v_weather_key = f_get_weather_key(v_weather_desc)

    # 1. 优先 Pexels
    if PEXELS_API_KEY:
        v_url = f_get_pexels_image(v_season, v_weather_key)
        if v_url:
            return v_url, "pexels"

    # 2. 名画兜底
    for v_key in [(v_season, v_weather_key), (v_season, "晴")]:
        if v_key in IMAGE_URLS and IMAGE_URLS[v_key]:
            return random.choice(IMAGE_URLS[v_key]), "wikimedia"
    return random.choice(FALLBACK_IMAGES), "fallback"


# ============================================================
# 主流程
# ============================================================
def f_main():
    v_today = date.today()

    # 1. 节气
    v_term = f_get_solar_term(v_today)
    v_season = f_get_season(v_term)

    # 2. 天气
    v_weather = f_get_weather("Wuhan")

    # 3. 诗句
    v_weather_desc = v_weather["desc"] if v_weather else ""
    v_poem_text, v_poem_author = f_get_poem(v_season, v_weather_desc)

    # 4. AI 一句话（可选，未配API Key则用预设）
    v_sentence = f_generate_sentence(v_weather, v_term)
    if not v_sentence:
        v_sentence = FALLBACK_SENTENCES.get(
            v_term, f"今日{v_term}，武汉的每一天都值得被记住。"
        )

    # 5. 图片
    v_image_url, v_image_source = f_get_image(v_season, v_weather_desc)

    # 6. 组装输出
    v_result = {
        "date": v_today.strftime("%Y-%m-%d"),
        "date_cn": f"{v_today.year}年{v_today.month}月{v_today.day}日",
        "weekday": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][v_today.weekday()],
        "solar_term": v_term,
        "season": v_season,
        "weather": v_weather,  # None 或 dict
        "poem": {"text": v_poem_text, "author": v_poem_author},
        "sentence": v_sentence,
        "image_url": v_image_url,
        "image_source": v_image_source,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 写入 data.json
    with open("data.json", "w", encoding="utf-8") as v_f:
        json.dump(v_result, v_f, ensure_ascii=False, indent=2)

    print(f"[OK] {v_result['date']} {v_term} → data.json")
    print(f"  天气: {v_weather['desc'] if v_weather else '未获取'}")
    print(f"  图片来源: {v_image_source}")
    print(f"  诗句: {v_poem_text}")
    print(f"  句子: {v_sentence}")
    return v_result


if __name__ == "__main__":
    f_main()
