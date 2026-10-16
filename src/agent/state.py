"""会话状态类型定义
继承 LangGraph 预构建的 AgentState（自带 messages / is_last_step / remaining_steps），
额外扩展业务字段。
"""
import operator
from typing import Annotated
from langgraph.prebuilt.chat_agent_executor import AgentState


class BaitState(AgentState):
    """在标准 AgentState 基础上扩展反诈业务字段。"""
    session_id: str
    caller_number: str
    victim_persona: dict
    scam_type: str
    stage: str
    turn_count: int
    # 线索列表：工具每次抽到新线索，用 reducer 累加
    leads: Annotated[list, operator.add]
