"""人设提示词加载器
提示词正文外置在 prompts/*.md（frontmatter 元数据 + 正文模板），
改人设只改文档、加新人设加一个 md，不用动代码——类似 skill 的组织方式。

md 文件格式：
    ---
    name: 王阿姨        # 元数据，对应 DEFAULT_PERSONA
    age: 62
    background: ...
    ---
    （正文 = 系统提示词模板，占位符：{name}{age}{background}{stage}{scam_type}{leads}）
"""
from pathlib import Path
import random

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_persona(slug: str = "wang_dama"):
    """读取人设文档，返回 (元数据 dict, 提示词模板 str)"""
    raw = (_PROMPTS_DIR / f"{slug}.md").read_text(encoding="utf-8")
    meta, body = {}, raw.strip()
    if raw.startswith("---"):
        _, front, body = raw.split("---", 2)
        for line in front.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = body.strip()
    return meta, body


def to_persona(meta: dict) -> dict:
    """frontmatter 元数据 → victim_persona 字典"""
    return {
        "name": meta.get("name", "王阿姨"),
        "real_name": meta.get("real_name", meta.get("name", "王阿姨")),
        "age": int(meta.get("age", "62")),
        "background": meta.get("background", ""),
    }


def list_personas() -> list[str]:
    """列出所有人设 slug（目录下每个 md 一个）"""
    return sorted(p.stem for p in _PROMPTS_DIR.glob("*.md"))


def load_random_persona() -> dict:
    """随机抽一个人设——每通来电随机分配，骗子摸不准对面是谁"""
    slug = random.choice(list_personas())
    return to_persona(load_persona(slug)[0])


# 性别指向称呼：骗子没点名但用了带性别的叫法时，按性别筛选人设
_FEMALE_HINTS = ("女士", "阿姨", "大妈", "大姐", "婶", "奶奶", "姑娘", "小姐", "太太", "姐")
_MALE_HINTS = ("先生", "大哥", "大爷", "大叔", "叔叔", "老板", "老总", "师傅", "哥们", "哥")


def pick_persona(first_sentence: str) -> dict:
    """根据骗子第一句话挑人设，避免'叫王阿姨、接刘老板'的穿帮。

    三级匹配：
      1. 骗子点名（说了某人设的 alias，如"王阿姨/刘总"）→ 直接应名
      2. 带性别指向的称呼（"女士/大爷/老板"）→ 同性别里随机
      3. 完全没指向 → 纯随机
    """
    metas = {s: load_persona(s)[0] for s in list_personas()}
    # 1. 点名应名
    for meta in metas.values():
        for alias in (meta.get("aliases") or "").split(","):
            if alias.strip() and alias.strip() in first_sentence:
                return to_persona(meta)
    # 2. 性别匹配
    if any(k in first_sentence for k in _FEMALE_HINTS):
        want = "女"
    elif any(k in first_sentence for k in _MALE_HINTS):
        want = "男"
    else:
        want = None
    if want:
        pool = [m for m in metas.values() if m.get("gender") == want]
        if pool:
            return to_persona(random.choice(pool))
    # 3. 纯随机
    return load_random_persona()


# 默认人设：导出接口与旧版保持一致（agent/graph.py 无需改动）
_meta, SYSTEM_PROMPT = load_persona()
DEFAULT_PERSONA = to_persona(_meta)
