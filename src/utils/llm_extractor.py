"""LLM 结构化抽取：LangChain Pydantic 模型 + JsonOutputParser

与正则兜底（extractor.py）互补：
- 类型清单从 lead_rules.json 动态生成 → 管理页加类型无需写正则，LLM 直接按枚举抽
- 用 Pydantic 对象定义抽取结果结构，JsonOutputParser 解析校验
- 纯提示词约束，不依赖端点的 response_format/function-calling 特性（各家兼容性不一），
  任何 OpenAI 兼容端点都能跑
"""
import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from utils.extractor import get_enabled_rules
from llm.chat_llm import llm

_parser = JsonOutputParser()


def _build_model(types: list) -> type:
    """按启用的类型动态生成 Pydantic 结果模型（type 字段做枚举校验）"""

    class Lead(BaseModel):
        type: str = Field(description=f"线索类型，只能取这些值之一：{types}")
        value: str = Field(description="线索原文，逐字照抄不要改写")
        confidence: float = Field(0.9, description="可信度 0~1")

    class LeadList(BaseModel):
        leads: List[Lead] = Field(default_factory=list, description="抽到的线索列表，没有则为空")

    return LeadList


def extract_leads_llm(text: str) -> List[dict]:
    """LLM 结构化抽取，返回 [{type, value, confidence}]；失败返回空列表（不阻断对话）"""
    rules = get_enabled_rules()
    if not rules:
        return []
    valid_types = {r["type"] for r in rules}
    type_menu = "；".join(f"{r['type']}={r['name']}" for r in rules)
    Model = _build_model(valid_types)
    prompt = (
        "你是反诈线索抽取器。从骗子的话术中抽出所有可疑线索"
        "（账号、卡号、链接、证件号、联系方式、钱包地址等）。\n"
        f"类型对照：{type_menu}\n"
        "严格按照 JSON 输出，不要输出任何其他文字，格式：\n"
        '{"leads": [{"type": "<类型标识>", "value": "<原文>", "confidence": 0.9}]}\n'
        '只抽骗子说出的信息，没有就输出 {"leads": []}。\n\n'
        f"骗子说：{text}"
    )
    try:
        data = _parser.parse(llm.invoke(prompt).content)
        leads = []
        for item in data.get("leads", []):
            if item.get("type") in valid_types and item.get("value"):
                leads.append({
                    "type": item["type"],
                    "value": str(item["value"]).strip(),
                    "confidence": float(item.get("confidence", 0.9)),
                })
        return leads
    except Exception:
        return []
