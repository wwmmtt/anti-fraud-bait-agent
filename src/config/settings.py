"""全局配置：读 .env，暴露给全项目

所有文件路径锚定项目根（src 的上一级），从任何目录启动都正确：
  python src/main.py / cd src && python main.py / python -m src.main 均可
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根 = src/config/settings.py 的上两级
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),  # .env 也锚定项目根
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 配置：任意 OpenAI 兼容服务都可接（DeepSeek / 通义 / Kimi / GLM / vLLM / ollama 的 OpenAI 端点）
    # 换模型只需改 .env 里的 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 三个值
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # 并发控制：同时最多打多少个 DeepSeek API 请求（高并发限流）
    max_concurrent_llm_calls: int = 10

    # 存储路径：默认锚定项目根；.env 里可用相对路径（自动转绝对）或绝对路径覆盖
    db_path: str = str(PROJECT_ROOT / "db" / "bait.db")
    faiss_index_path: str = str(PROJECT_ROOT / "db" / "faiss_index")
    embedding_model_path: str = str(PROJECT_ROOT / "model" / "bge-base-zh-v1.5")
    seed_data_dir: str = str(PROJECT_ROOT / "src" / "rag" / "seed_data")

    # 服务
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
