"""Agent 工具集：Agent 自主决定调哪个工具
- 工具内部处理副作用（写库、更新状态）
- session_id 通过 RunnableConfig 的 thread_id 注入（调用方用 config 传入）
- 需要更新状态的工具返回 Command，并附带 ToolMessage（用 InjectedToolCallId 规范注入）
"""
from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from rag.vector_store import search_similar
from utils.extractor import extract_all_leads
from storage.sqlite_client import insert_lead, check_entity_exists


@tool
def rag_scam_playbook(query: str) -> str:
    """检索诈骗剧本知识库，返回同类骗局的话术参考。
    当你不确定骗子套路、不知道怎么应对时调用。"""
    try:
        results = search_similar(query, k=3)
        if not results:
            return "知识库暂无相关剧本。"
        return "\n---\n".join([f"[参考{i+1}] {r}" for i, r in enumerate(results)])
    except Exception as e:
        # 向量库没初始化也不能让 Agent 崩
        return f"知识库检索失败，按你的理解继续应对。（错误：{e}）"


@tool
def extract_leads(
    text: str,
    config: RunnableConfig,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """从对话文本中抽取可疑线索（当前启用的线索类型见系统提示清单）。
    对方报出卡号、账号、网址、证件号等任何线索信息时调用。"""
    session_id = config["configurable"].get("thread_id", "")
    # 双通道：正则快路径（零成本） + LLM 结构化输出（补漏口语化表达），按 (type, value) 去重
    from utils.llm_extractor import extract_leads_llm
    leads = extract_all_leads(text)
    seen = {(l["type"], l["value"]) for l in leads}
    for lead in extract_leads_llm(text):
        if (lead["type"], lead["value"]) not in seen:
            seen.add((lead["type"], lead["value"]))
            leads.append(lead)
    for lead in leads:
        if not check_entity_exists(lead["value"]):  # 查重，避免与正则兜底重复入库
            insert_lead(
                session_id=session_id,
                lead_type=lead["type"],
                lead_value=lead["value"],
                confidence=lead.get("confidence", 0.5),
                turn=0,
            )
    msg = f"抽到 {len(leads)} 条线索：{leads}" if leads else "本轮未抽到资金线索。"
    # 同时把线索更新到 state（leads 用 operator.add reducer 累加），并回 ToolMessage 响应 tool_call
    return Command(
        update={
            "leads": leads,
            "messages": [ToolMessage(content=msg, tool_call_id=tool_call_id)],
        }
    )


@tool
def update_stage(
    new_stage: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """更新对话阶段。可选值：
    greeting(刚接通) / scam_pitch(骗子宣讲剧本) / ask_money(要求转账) /
    ask_account(索要收款账号) / suspicious(骗子怀疑我是AI) / ended。"""
    return Command(
        update={
            "stage": new_stage,
            "messages": [
                ToolMessage(
                    content=f"对话阶段已更新为：{new_stage}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def check_known_entity(value: str) -> str:
    """查重：这个卡号/网址/钱包之前见过吗？查已知诈骗实体库。"""
    try:
        exists = check_entity_exists(value)
        return "已知实体，之前出现过" if exists else "新实体，首次出现"
    except Exception:
        return "查重失败，按新实体处理。"


ALL_TOOLS = [rag_scam_playbook, extract_leads, update_stage, check_known_entity]
