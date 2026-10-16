# 🎣 Anti-Fraud Bait Agent

English | [简体中文](README.zh-CN.md)

> An AI agent that pretends to be an easy-to-scam elderly victim,
> keeps scammers talking for 20+ minutes, and silently harvests their
> bank card numbers, crypto wallet addresses, and phishing URLs —
> so they have no time to harass real people.

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3-red.svg)](https://github.com/langchain-ai/langgraph)
[![LLM: DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-green.svg)](https://platform.deepseek.com/)

---

##  Why this project

Traditional anti-fraud works like this:

```
Scammer calls → telecom signals flag it → call gets dropped
```

Problem: ban one number, the scammer burns ten new ones. **The scammer's time
cost is near zero, our defensive cost keeps climbing.**

This project flips the playbook — instead of hanging up, route the flagged call
to an AI virtual victim and let it chat with the scammer:

```
Scammer calls → signal detection → routed to AI "Auntie Wang"
              → plays dumb for 20 min
              → extracts card no. / wallet / phishing URL
              → hands leads to banks & cyber-police to freeze cards / sink domains
```

Inspired by [Apate](https://apate.ai) (Australia, 2.5M scammer conversations,
170K scammer-hours burned, $8.15M seed). This repo is an open-source
re-implementation — runnable on your laptop.

**We don't block the scammer's call. We burn the scammer's working hours and
cut off their money-laundering pipeline.**

---

## ✨ What makes this different

| Dimension | Traditional anti-fraud | This project |
|---|---|---|
| What you do to the scammer | Hang up | **Chat with them for 20 min, extract leads** |
| Output | Blocked-call logs | **Bank cards, crypto wallets, phishing URLs, scripts** |
| Closed loop | Block the call | **Freeze cards / sink domains / break laundering** |
| Tech form | Rule engine | **Real ReAct Agent (LangGraph self-directed tool calls)** |

This is not a hardcoded script bot. The agent:

- Calls the **RAG tool** when it doesn't recognize a scam pattern
- Calls the **lead-extraction tool** when the scammer mentions a card/wallet/URL
- Calls the **stage-update tool** as the conversation progresses
- Calls the **entity-check tool** to flag known-bad accounts

---

## 🚀 Quick start

```bash
# 1. Clone & install
git clone <your-repo>
cd anti-fraud-bait
pip install -r requirements.txt

# 2. Set LLM API key (or skip if LLM_API_KEY is already in your env)
export LLM_API_KEY="sk-your-key"        # Linux / macOS
$env:LLM_API_KEY="sk-your-key"          # Windows PowerShell

# 3. Download the embedding model (390MB, gitignored; put it in model/bge-base-zh-v1.5/)
pip install modelscope
modelscope download --model BAAI/bge-base-zh-v1.5 --local_dir model/bge-base-zh-v1.5
# Or HuggingFace: huggingface-cli download BAAI/bge-base-zh-v1.5 --local-dir model/bge-base-zh-v1.5

# 4. Run (vector index builds / syncs new docs automatically on startup)
python src/demo_cli.py  # CLI: chat with "Auntie Wang" in the terminal
python src/main.py      # or serve HTTP: API docs at /docs, leads dashboard at /leads
```

> The LLM is swappable — any OpenAI-compatible endpoint (DeepSeek / Qwen /
> Kimi / GLM / vLLM) works by editing `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY`
> in `.env`. DeepSeek is dirt cheap — running this demo all day costs pennies.

---

## 🎯 Test scenarios

See [`test_scripts.md`](test_scripts.md) — six realistic multi-turn scripts:
impostor police, part-time rebate, fake customer service, impostor relative,
counter-intelligence test, and a 15-turn combined stress test.

---

## 🏗️ Project layout

```
anti-fraud-bait/
├── src/                     # All source code (src layout)
│   ├── main.py              # FastAPI entry
│   ├── demo_cli.py          # CLI for quick testing
│   ├── agent/               # 🧠 Agent core (LangGraph create_react_agent)
│   │   ├── state.py         #   State schema (extends AgentState)
│   │   ├── prompts.py       #   Auntie Wang persona + system prompt
│   │   ├── tools.py         #   4 tools: RAG / extract_leads / update_stage / check_entity
│   │   └── graph.py         #   create_react_agent + run_turn wrapper
│   ├── llm/chat_llm.py      # LLM client (any OpenAI-compatible endpoint via .env)
│   ├── rag/                 # FAISS vector store + scam playbook KB
│   │   ├── vector_store.py
│   │   └── seed_data/       #   5 sample scam scripts
│   ├── storage/             # SQLite (sessions / messages / leads)
│   ├── api/                 # FastAPI routers + chat page + leads dashboard
│   ├── config/              # pydantic-settings
│   └── utils/               # Regex extractor, logger
├── test_scripts.md          # Realistic scammer scripts
├── requirements.txt
├── model/                   # Local embedding model (bge-base-zh-v1.5)
├── db/                      # SQLite file + FAISS index (gitignored)
└── logs/                    # Runtime logs
```

---

## ⚠️ Scope & boundary (read this first)

> This is currently a **text-only Agent capability validation demo**.

**It cannot receive real scam calls yet.** To intercept real calls you need
carrier cooperation:

1. Carrier flags high-risk calls at the core network
2. The call is **rerouted to this system before reaching the victim's phone**
3. A SIP gateway + ASR (speech-to-text) + TTS (text-to-speech) layer is bolted on

```
Real phone pipeline (future work):
Carrier → SIP → ASR → /turn API → TTS → play to scammer
```

This repo validates the middle `/turn` piece — **is the agent smart enough to
impersonate a victim, stall the scammer, and extract leads?**
Once that layer works, wrapping it with a voice pipeline is just two more API calls.

**Without carrier core-network routing, this stays a text demo forever.**
That's the real bottleneck for production-grade anti-fraud in China — not the AI.

---

## 📈 Production hardening

| Component | Demo | Production |
|---|---|---|
| Session state | MemorySaver (in-process) | **RedisSaver** (shared across workers) |
| DB | SQLite WAL | **PostgreSQL + connection pool** |
| Vector store | Local FAISS file | Read-only replicas, naturally concurrent-safe |
| Web | FastAPI async | uvicorn/gunicorn multi-worker |
| Voice pipeline | None | SIP + ASR + TTS |

---

## 🤝 Contributing

- **Add a scam script**: drop a `.txt` into `rag/seed_data/` and restart — auto-indexed incrementally (no manual init, no index deletion)
- **Add a tool**: write a `@tool` function in `agent/tools.py`, the agent picks it up
- **Add a persona**: drop a new `src/agent/prompts/<name>.md` (frontmatter + prompt body, like a skill) — no code changes needed
- **Swap LLM**: edit `.env`, any OpenAI-compatible endpoint works
- **Hook up real phones**: attach SIP/ASR in front of `/turn`, text layer stays untouched

Forks are welcome — especially to grow `rag/seed_data/` and make the persona
even more convincing.

---

##  License

[**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/deed.zh)

- ✅ Personal use, study, research, modification, fork & grow
- ❌ No commercial use
- 📌 Keep attribution

---

## 🔗 References

- Apate (Australia): [apate.ai](https://apate.ai)
- LangGraph `create_react_agent`: [docs](https://langchain-ai.github.io/langgraph/reference/prebuilt/)
