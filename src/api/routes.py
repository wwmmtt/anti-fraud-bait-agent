"""FastAPI 路由：对外提供三个接口"""
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from agent.graph import run_turn
from storage.sqlite_client import get_session_leads
from utils.logger import logger

router = APIRouter()


class StartRequest(BaseModel):
    caller_number: str = "unknown"


class TurnRequest(BaseModel):
    session_id: str
    scammer_text: str
    caller_number: str = ""


@router.post("/session/start")
def start_session(req: StartRequest):
    """开启新会话，返回 session_id"""
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    logger.info(f"新会话开启: {session_id}, 来电: {req.caller_number}")
    return {"session_id": session_id, "status": "started"}


@router.post("/turn")
async def turn(req: TurnRequest):
    """输入骗子的话，AI 返回伪装受害者的回复（async，天然高并发）"""
    result = run_turn(req.session_id, req.scammer_text, req.caller_number)
    return {
        "reply_text": result["reply"],
        "leads_found": result["leads"],
        "stage": result["stage"],
        "turn_count": result["turn_count"],
    }


@router.post("/session/end")
def end_session(session_id: str):
    """结束会话，导出全量线索"""
    leads = get_session_leads(session_id)
    logger.info(f"会话结束: {session_id}, 共 {len(leads)} 条线索")
    return {"session_id": session_id, "status": "ended", "leads": leads}
