"""SQLite 表结构定义"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    caller_number TEXT,
    persona TEXT,
    scam_type TEXT DEFAULT 'unknown',
    stage TEXT DEFAULT 'greeting',
    turn_count INTEGER DEFAULT 0,
    -- SQLite 的 CURRENT_TIMESTAMP 是 UTC，比北京时间慢 8 小时，这里用本地时间
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    ended_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content TEXT,
    turn_number INTEGER,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    lead_type TEXT,
    lead_value TEXT,
    confidence REAL DEFAULT 0.5,
    turn_number INTEGER,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_session ON leads(session_id);
CREATE INDEX IF NOT EXISTS idx_leads_value ON leads(lead_value);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""
