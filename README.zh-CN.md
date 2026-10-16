# 🎣 反诈诱饵 Agent / Anti-Fraud Bait Agent

[English](README.md) | 简体中文

> AI 假扮容易上当的老人，反过来陪骗子聊 20 分钟——把骗子的工时耗光，
> 把骗子的银行卡号、加密钱包、钓鱼网址套出来，交给银行冻卡、交给反诈中心打击。

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3-red.svg)](https://github.com/langchain-ai/langgraph)
[![LLM: DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-green.svg)](https://platform.deepseek.com/)

---

## 💡 为什么做这个

传统反诈思路是：

```
骗子来电 → 信令识别 → 挂断
```

问题：封一个号，骗子换十个新号继续打。**骗子的时间成本趋近于零，
我们的防御成本越来越高。**

这个项目换了个打法——识别出诈骗电话后不挂，转交给 AI 虚拟受害者陪他聊：

```
骗子来电 → 信令识别 → 转给AI"王阿姨"
        → 装傻拖延 20 分钟
        → 套出卡号 / 钱包 / 钓鱼网址
        → 交给银行、反诈中心冻卡、封域名
```

参考澳洲 [Apate](https://apate.ai)（250 万次骗子对话、消耗骗子 17 万工时、
种子轮 815 万美元），用开源技术栈重新实现，笔记本电脑就能跑。

**不是挡骗子的电话，是消耗骗子的工时，端掉骗子的资金链路。**

---

## ✨ 这个项目有什么不一样

| 维度 | 传统反诈 | 本项目 |
|---|---|---|
| 对骗子的动作 | 挂断 | **陪聊 20 分钟，套取资金线索** |
| 产出 | 拦截日志 | **银行卡号、加密钱包、钓鱼网址、话术剧本** |
| 反诈闭环 | 挡电话 | **源头冻卡、封域名、切断洗钱链路** |
| 技术形态 | 规则引擎 | **真·ReAct Agent（LangGraph 自主工具调用）** |

不是写死的话术库：
- 遇到不认识的套路，**自己调 RAG 工具**查剧本库
- 骗子报出卡号，**自己调抽取工具**落库
- 对话推进到新阶段，**自己调状态工具**更新阶段
- 骗子报的网址/卡号，**自己调查重工具**判断是不是新实体

---

## 🚀 快速开始

```bash
# 1. 克隆 & 装依赖
git clone <你的仓库地址>
cd anti-fraud-bait
pip install -r requirements.txt

# 2. 配置 LLM API Key（环境变量里已有 LLM_API_KEY 则跳过）
export LLM_API_KEY="sk-你的key"         # Linux / macOS
$env:LLM_API_KEY="sk-你的key"           # Windows PowerShell

# 3. 下载 embedding 模型（390MB，已 gitignore；放进 model/bge-base-zh-v1.5/）
pip install modelscope
modelscope download --model BAAI/bge-base-zh-v1.5 --local_dir model/bge-base-zh-v1.5
# 或 HuggingFace: huggingface-cli download BAAI/bge-base-zh-v1.5 --local-dir model/bge-base-zh-v1.5

# 4. 跑起来（向量库启动时自动构建，无需手动初始化）
python src/demo_cli.py  # 终端直接跟"王阿姨"对话
python src/main.py      # 或起 HTTP 服务：API 文档 /docs，线索后台 /leads
```

> LLM 可随意更换——任何 OpenAI 兼容接口（DeepSeek / 通义 / Kimi / GLM / vLLM）
> 改 `.env` 里的 `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` 三个值即可。
> DeepSeek 一百万 token 几块钱，跑一整天 demo 不到一块钱。

---

## 🎯 测试话术

见 [`test_scripts.md`](test_scripts.md)，6 类真实剧本多轮对话：
冒充公检法、刷单返利、客服退款、冒充熟人车祸、反侦察测试、15 轮长对话压测。
把骗子台词一行行粘到命令行即可。

---

## 🏗️ 项目结构

```
anti-fraud-bait/
├── src/                     # 全部源码（src layout 规范）
│   ├── main.py              # FastAPI 入口
│   ├── demo_cli.py          # 命令行交互
│   ├── agent/               # 🧠 Agent 核心（LangGraph create_react_agent）
│   │   ├── state.py         #   状态定义（继承 AgentState）
│   │   ├── prompts.py       #   王阿姨人设 + 系统提示
│   │   ├── tools.py         #   4 个工具：RAG / 抽线索 / 阶段流转 / 实体查重
│   │   └── graph.py         #   create_react_agent + run_turn 封装
│   ├── llm/chat_llm.py      # LLM 客户端（.env 配置任意 OpenAI 兼容接口）
│   ├── rag/                 # FAISS 向量库 + 诈骗剧本知识库
│   │   ├── vector_store.py
│   │   └── seed_data/       #   4 类诈骗剧本样本
│   ├── storage/             # SQLite（sessions/messages/leads 三表）
│   ├── api/                 # FastAPI 路由 + 聊天页 + 线索后台页面
│   ├── config/              # pydantic-settings 配置
│   └── utils/               # 正则抽取、日志
├── test_scripts.md          # 真实诈骗话术集
├── requirements.txt
├── model/                   # 本地 embedding 模型（bge-base-zh-v1.5）
├── db/                      # SQLite 文件 + FAISS 索引（已 gitignore）
└── logs/                    # 运行日志
```

---

## ⚠️ 项目边界（重要）

> 当前是**纯文本 Agent 能力验证 Demo**。

**它现在接不到真实诈骗电话**——真要接电话需要运营商配合：

1. 运营商在核心网侧识别高危来电
2. 把呼叫在到达真人手机之前**路由重定向**到本系统
3. 前面再包一层 SIP 网关 + ASR（语音转文字）+ TTS（文字转语音）

```
真实电话链路（未来要做的）：
运营商 → SIP 网关 → ASR → /turn 接口 → TTS → 播给骗子
```

这个项目验证的是中间那一段 `/turn` 接口里的 Agent 够不够聪明——
能不能装得像、能不能拖住、能不能套出卡号。
跑通这层，外面包语音管道就是加两个 API 调用的事。

**没有运营商核心网路由权限，这个项目永远是个文本 Demo。**
这是国内反诈落地最大的卡点，不是 AI 技术问题。

---

## 📈 生产化扩展点

| 组件 | Demo | 生产方案 |
|---|---|---|
| 会话状态 | MemorySaver（内存） | **RedisSaver**（多 worker 共享） |
| 数据库 | SQLite WAL | **PostgreSQL + 连接池** |
| 向量库 | FAISS 本地文件 | 多副本只读，天然并发安全 |
| Web 服务 | FastAPI async | uvicorn/gunicorn 多 worker |
| 语音管道 | 无 | SIP + ASR + TTS |

---

## 🤝 二次开发

这个项目就是拿来折腾的：

- **加新诈骗剧本**：往 `rag/seed_data/` 扔一个 txt，删掉 `db/faiss_index/` 重启（自动重建）
- **加新工具**：在 `agent/tools.py` 写个 `@tool` 函数，Agent 自动学会用
- **换受害者人设**：在 `src/agent/prompts/` 加一个 md 文档（frontmatter 元数据 + 提示词正文，类似 skill），不用改代码
- **换 LLM**：改 `.env` 三个值，任何 OpenAI 兼容接口都能插
- **接真实电话**：在 `/turn` 前面接 SIP/ASR，文本层不用动

欢迎 fork 后壮大——尤其是把 `rag/seed_data/` 喂得更丰富、把 Agent 调得更像真人。

---

## 📜 协议

[**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/deed.zh)

- ✅ 个人使用、学习、研究、修改、二次开发
- ❌ 禁止商业用途
- 📌 保留原作者署名

---

## 🔗 参考

- Apate (Australia): [apate.ai](https://apate.ai)
- LangGraph `create_react_agent`: [docs](https://langchain-ai.github.io/langgraph/reference/prebuilt/)
