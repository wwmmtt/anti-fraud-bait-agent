"""FAISS 向量库：加载诈骗剧本，相似度检索
用 HuggingFaceEmbeddings 直接加载本地原始模型包（model/bge-base-zh-v1.5），
不依赖 ollama 服务。
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings

# 高并发：FAISS 是只读检索，多线程并发读安全，无需加锁
_vector_store = None
_embeddings = None


def _get_embeddings():
    """加载本地 bge embedding 模型目录（HuggingFace 原始格式）"""
    global _embeddings
    if _embeddings is None:
        model_path = settings.embedding_model_path
        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"本地 embedding 模型目录不存在: {model_path}")
        _embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={"device": "cpu"},   # torch 为 CPU 版；有 GPU 可改 "cuda"
            encode_kwargs={"normalize_embeddings": True},  # bge 官方建议归一化，配合内积/余弦检索
        )
    return _embeddings


def init_vector_store():
    """从 seed_data 目录加载所有诈骗剧本 txt，构建 FAISS 索引"""
    texts = []
    for fname in os.listdir(settings.seed_data_dir):
        if fname.endswith(".txt"):
            fpath = os.path.join(settings.seed_data_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                texts.append(f.read())

    if not texts:
        raise RuntimeError("seed_data 目录下没有诈骗剧本 txt 文件")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text("\n\n".join(texts))

    global _vector_store
    _vector_store = FAISS.from_texts(chunks, _get_embeddings())
    _vector_store.save_local(settings.faiss_index_path)
    print(f"FAISS 索引已构建，共 {len(chunks)} 个文本块")


def ensure_vector_store():
    """确保向量库就绪：有索引就加载，没有就自动构建。启动时调用，用户无感。"""
    global _vector_store
    if _vector_store is not None:
        return
    if os.path.exists(settings.faiss_index_path):
        _vector_store = FAISS.load_local(
            settings.faiss_index_path,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        print(f"FAISS 索引已加载：{settings.faiss_index_path}")
    else:
        init_vector_store()


def search_similar(query: str, k: int = 3):
    """相似度检索：返回最相关的 k 段诈骗剧本"""
    global _vector_store
    ensure_vector_store()

    docs = _vector_store.similarity_search(query, k=k)
    return [d.page_content for d in docs]
