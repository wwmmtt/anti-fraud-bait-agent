"""反诈诱饵 Agent：基于 LangGraph 官方预构建的 create_react_agent

不手写图，直接用官方 ReAct 实现：
  Agent 决策 → 条件边 → 工具执行 → 回到 Agent → ... → 生成回复
"""
import json
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.state import BaitState
from agent.prompts import SYSTEM_PROMPT, DEFAULT_PERSONA, pick_persona
from agent.tools import ALL_TOOLS
from llm.chat_llm import llm
from storage.sqlite_client import insert_session, insert_message, update_session

# 高并发扩展点：生产把 MemorySaver 换成 RedisSaver，多 worker 共享会话状态
checkpointer = MemorySaver()


def build_prompt(state: BaitState):
    """动态系统提示：函数模式必须返回完整消息列表（系统消息 + 历史消息）"""
    persona = state.get("victim_persona") or DEFAULT_PERSONA
    leads = state.get("leads", [])
    leads_str = json.dumps(leads, ensure_ascii=False) if leads else "暂无"
    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(
        name=persona.get("name", "王阿姨"),
        real_name=persona.get("real_name", persona.get("name", "王阿姨")),
        age=persona.get("age", 62),
        background=persona.get("background", ""),
        stage=state.get("stage", "greeting"),
        scam_type=state.get("scam_type", "unknown"),
        leads=leads_str,
    ))
    # 抽取规则可在管理页动态增删改，这里把当前启用的类型注入系统提示，LLM 即时感知
    from utils.extractor import enabled_types_str
    system_msg.content += (
        f"\n\n【需抽取的线索类型】\n{enabled_types_str()}。"
        "对方提到以上任何信息时，必须调用 extract_leads 工具抽取。"
    )
    return [system_msg] + list(state.get("messages", []))


# 官方预构建 ReAct Agent
bait_agent = create_react_agent(
    model=llm,
    tools=ALL_TOOLS,
    prompt=build_prompt,
    state_schema=BaitState,
    checkpointer=checkpointer,
)


def run_turn(session_id: str, scammer_text: str, caller_number: str = "") -> dict:
    """处理一轮对话。首轮自动初始化会话，后续轮次自动恢复状态。

    入参：
      session_id   : 会话ID（同时作为 checkpointer 的 thread_id）
      scammer_text : 骗子本轮说的话
      caller_number: 来电号码（首轮使用）
    出参：
      {"reply": str, "leads": list, "stage": str, "turn_count": int}
    """
    config = {"configurable": {"thread_id": session_id}}

    # 检查是否已有会话状态，没有则首轮初始化：按骗子第一句话挑人设（点名应名→性别匹配→随机）
    existing = bait_agent.get_state(config)
    if existing is None or not existing.values:
        persona = pick_persona(scammer_text)
        insert_session(session_id, caller_number, json.dumps(persona, ensure_ascii=False))
        payload = {
            "messages": [HumanMessage(content=scammer_text)],
            "session_id": session_id,
            "caller_number": caller_number,
            "victim_persona": persona,
            "scam_type": "unknown",
            "stage": "greeting",
            "turn_count": 0,
            "leads": [],
        }
    else:
        payload = {"messages": [HumanMessage(content=scammer_text)]}

    result = bait_agent.invoke(payload, config=config)

    # 取最后一条 AI 消息作为回复
    reply = result["messages"][-1]
    reply_text = reply.content if isinstance(reply, AIMessage) else str(reply.content)

    # 轮数：骗子每轮发一条 HumanMessage，直接数
    turn_count = sum(1 for m in result["messages"] if isinstance(m, HumanMessage))

    # 确定性正则兜底：每轮强制抽一次骗子的话（不依赖 LLM 是否主动调工具）
    from utils.extractor import extract_all_leads
    from storage.sqlite_client import insert_lead, check_entity_exists
    forced_leads = extract_all_leads(scammer_text)
    for lead in forced_leads:
        if not check_entity_exists(lead["value"]):  # 查重，避免工具+兜底重复入库
            insert_lead(
                session_id=session_id,
                lead_type=lead["type"],
                lead_value=lead["value"],
                confidence=lead.get("confidence", 0.5),
                turn=turn_count,
            )

    # 合并工具抽取与正则兜底的结果，按 (type, value) 去重
    seen = set()
    all_leads = []
    for lead in list(result.get("leads", [])) + forced_leads:
        key = (lead["type"], lead["value"])
        if key not in seen:
            seen.add(key)
            all_leads.append(lead)

    # 对话记录持久化 + 会话状态同步到 DB
    insert_message(session_id, "scammer", scammer_text, turn_count)
    insert_message(session_id, "bait", reply_text, turn_count)
    update_session(
        session_id,
        stage=result.get("stage", "greeting"),
        turn_count=turn_count,
    )

    return {
        "reply": reply_text,
        "leads": all_leads,
        "stage": result.get("stage", "greeting"),
        "turn_count": turn_count,
    }
