"""SQLite 连接与 CRUD
高并发扩展点：SQLite 是单写锁，生产高并发写入换 PostgreSQL/MySQL。
"""
import sqlite3
import threading
from config.settings import settings
from storage.models import SCHEMA

# 每线程独立连接：FastAPI threadpool 多线程共用一个 connection 会并发崩溃
_local = threading.local()


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(
            settings.db_path,
            timeout=10,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(SCHEMA)  # 幂等建表
        _local.conn = conn
    return conn


# ===== 会话 =====

def insert_session(session_id: str, caller_number: str, persona: str):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (session_id, caller_number, persona) VALUES (?, ?, ?)",
        (session_id, caller_number, persona),
    )
    conn.commit()


def update_session(session_id: str, **kwargs):
    conn = get_conn()
    for k, v in kwargs.items():
        conn.execute(f"UPDATE sessions SET {k}=? WHERE session_id=?", (v, session_id))
    conn.commit()


def get_all_sessions():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, COUNT(DISTINCT l.id) as lead_count
        FROM sessions s
        LEFT JOIN leads l ON s.session_id = l.session_id
        GROUP BY s.session_id
        ORDER BY s.created_at DESC
    """).fetchall()
    return [dict(r) for r in rows]


# ===== 对话记录 =====

def insert_message(session_id: str, role: str, content: str, turn: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, turn_number) VALUES (?, ?, ?, ?)",
        (session_id, role, content, turn),
    )
    conn.commit()


def get_session_messages(session_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# ===== 线索 =====

def insert_lead(session_id: str, lead_type: str, lead_value: str, confidence: float, turn: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO leads (session_id, lead_type, lead_value, confidence, turn_number) VALUES (?, ?, ?, ?, ?)",
        (session_id, lead_type, lead_value, confidence, turn),
    )
    conn.commit()


def check_entity_exists(value: str) -> bool:
    conn = get_conn()
    cur = conn.execute("SELECT 1 FROM leads WHERE lead_value = ? LIMIT 1", (value,))
    return cur.fetchone() is not None


def get_session_leads(session_id: str):
    conn = get_conn()
    cur = conn.execute("SELECT * FROM leads WHERE session_id = ?", (session_id,))
    return [dict(r) for r in cur.fetchall()]


def get_all_leads(lead_type: str = "", session_id: str = ""):
    conn = get_conn()
    sql = "SELECT * FROM leads WHERE 1=1"
    params = []
    if lead_type:
        sql += " AND lead_type=?"
        params.append(lead_type)
    if session_id:
        sql += " AND session_id=?"
        params.append(session_id)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_lead_stats():
    """统计各类线索数量"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT lead_type, COUNT(*) as count
        FROM leads
        GROUP BY lead_type
    """).fetchall()
    stats = {r["lead_type"]: r["count"] for r in rows}
    stats["total"] = sum(stats.values())
    stats["sessions"] = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    return stats
