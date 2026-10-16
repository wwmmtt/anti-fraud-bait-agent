"""线索抽取：规则可配置（config/lead_rules.json）
- 管理页面可增/删/改/启停规则，实时生效（无需重启）
- enabled 且配了 regex 的规则走正则确定性抽取；没配 regex 的类型仅靠 LLM 抽取
"""
import json
import re
from pathlib import Path
from typing import List, Dict

RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "lead_rules.json"


def load_rules() -> list:
    """读取全部抽取规则"""
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def save_rules(rules: list):
    """写回抽取规则（管理页面调用）"""
    RULES_PATH.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_enabled_rules() -> list:
    return [r for r in load_rules() if r.get("enabled", True)]


def enabled_types_str() -> str:
    """当前启用的线索类型清单（注入 Agent 系统提示）"""
    return "、".join(f"{r['name']}({r['type']})" for r in get_enabled_rules()) or "无"


def extract_all_leads(text: str) -> List[Dict]:
    """按启用的规则从文本中抽取线索，返回 [{type, value, confidence}]"""
    leads = []
    for rule in get_enabled_rules():
        pattern = rule.get("regex")
        if not pattern:
            continue  # 没配正则的类型交给 LLM 抽
        try:
            for m in re.findall(pattern, text):
                leads.append({
                    "type": rule["type"],
                    "value": m,
                    "confidence": rule.get("confidence", 0.8),
                })
        except re.error:
            continue  # 管理页写错正则也不能让对话崩

    # 同一取值命中多条规则时，只保留可信度最高的类型
    # （例：18位身份证号也会匹配 16-19 位的银行卡正则，按可信度归到身份证）
    best: Dict[str, Dict] = {}
    for lead in leads:
        if lead["value"] not in best or lead["confidence"] > best[lead["value"]]["confidence"]:
            best[lead["value"]] = lead
    return list(best.values())
