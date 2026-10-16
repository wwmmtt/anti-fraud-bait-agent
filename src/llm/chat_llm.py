"""LLM 初始化（OpenAI 兼容协议，可随意更换模型服务商）

换模型只改 .env 三个值，代码不用动：
  LLM_API_KEY=sk-xxx
  LLM_BASE_URL=https://api.deepseek.com/v1     # 或通义/Kimi/GLM/vLLM/ollama 等兼容端点
  LLM_MODEL=deepseek-chat                      # 对应服务商的模型名
"""
from langchain_openai import ChatOpenAI
from config.settings import settings

# 全项目共用一个 LLM 实例
# 高并发：httpx 底层自带连接池，多请求复用连接
llm = ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    temperature=0.7,
    timeout=30,
)
