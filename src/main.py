"""应用入口：启动 FastAPI 服务"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes import router
from api.leads_page import router as leads_router
from api.chat_page import router as chat_router
from config.settings import settings
from utils.logger import logger
from rag.vector_store import ensure_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """后台线程预加载向量库：网页秒开，模型在后台就绪"""
    import threading
    threading.Thread(target=ensure_vector_store, daemon=True).start()
    yield


app = FastAPI(title="Anti-Fraud Bait Agent", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.include_router(leads_router)
app.include_router(chat_router)


@app.get("/")
def health():
    return {"status": "ok", "service": "anti-fraud-bait-agent", "leads_page": "/leads"}


if __name__ == "__main__":
    import uvicorn
    logger.info(f"服务启动在 http://{settings.host}:{settings.port}")
    logger.info(f"线索管理页面: http://localhost:{settings.port}/leads")
    uvicorn.run(app, host=settings.host, port=settings.port)
