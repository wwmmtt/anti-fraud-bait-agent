"""FAISS 向量库：加载诈骗剧本，相似度检索
用 HuggingFaceEmbeddings 直接加载本地原始模型包（model/bge-base-zh-v1.5），
不依赖 ollama 服务。
"""
import json
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


def _manifest_path():
    return os.path.join(settings.faiss_index_path, "manifest.json")


def _load_manifest():
    """已索引文件清单：{filename: {mtime, chunks}}"""
    p = _manifest_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_manifest(m):
    os.makedirs(settings.faiss_index_path, exist_ok=True)
    with open(_manifest_path(), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def _scan_seed_dir():
    """扫描 seed_data 目录，返回 {filename: mtime}"""
    files = {}
    if os.path.isdir(settings.seed_data_dir):
        for fname in os.listdir(settings.seed_data_dir):
            if fname.endswith(".txt"):
                fpath = os.path.join(settings.seed_data_dir, fname)
                files[fname] = os.path.getmtime(fpath)
    return files


def sync_vector_store():
    """增量同步：新增 txt 自动切分入库；删除或修改的文件触发全量重建保证一致。
    启动时由 ensure_vector_store 自动调用，用户往 seed_data 扔新文档重启即可。
    """
    global _vector_store
    if _vector_store is None:
        return
    files = _scan_seed_dir()
    manifest = _load_manifest()
    new_files, need_rebuild = [], False
    for name, mtime in files.items():
        rec = manifest.get(name)
        if rec is None:
            new_files.append(name)
        elif rec.get("mtime") != mtime:
            need_rebuild = True
    for name in manifest:
        if name not in files:  # 被删除
            need_rebuild = True
    if need_rebuild:
        _vector_store = None
        if os.path.exists(settings.faiss_index_path):
            import shutil
            shutil.rmtree(settings.faiss_index_path)
        init_vector_store()
        return
    if new_files:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        for name in new_files:
            with open(os.path.join(settings.seed_data_dir, name), "r", encoding="utf-8") as f:
                chunks = splitter.split_text(f.read())
            if chunks:
                _vector_store.add_texts(chunks, metadatas=[{"source": name}] * len(chunks))
                manifest[name] = {"mtime": files[name], "chunks": len(chunks)}
        _vector_store.save_local(settings.faiss_index_path)
        _save_manifest(manifest)
        print(f"FAISS 增量入库 {len(new_files)} 个新文档：{new_files}")


def init_vector_store():
    """从 seed_data 目录加载所有诈骗剧本 txt，构建 FAISS 索引（全量）"""
    texts = []
    manifest = {}
    files = _scan_seed_dir()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks_all = []
    for name in files:
        with open(os.path.join(settings.seed_data_dir, name), "r", encoding="utf-8") as f:
            chunks = splitter.split_text(f.read())
        chunks_all.extend(chunks)
        manifest[name] = {"mtime": files[name], "chunks": len(chunks)}

    if not chunks_all:
        raise RuntimeError("seed_data 目录下没有诈骗剧本 txt 文件")

    global _vector_store
    _vector_store = FAISS.from_texts(chunks_all, _get_embeddings())
    os.makedirs(settings.faiss_index_path, exist_ok=True)
    _vector_store.save_local(settings.faiss_index_path)
    _save_manifest(manifest)
    print(f"FAISS 索引已构建，共 {len(chunks_all)} 个文本块")


def ensure_vector_store():
    """确保向量库就绪：有索引就加载并增量同步新文档，没有就自动构建。启动时调用，用户无感。"""
    global _vector_store
    if _vector_store is not None:
        return
    if os.path.exists(settings.faiss_index_path) and os.path.exists(
        os.path.join(settings.faiss_index_path, "index.faiss")
    ):
        _vector_store = FAISS.load_local(
            settings.faiss_index_path,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        print(f"FAISS 索引已加载：{settings.faiss_index_path}")
        sync_vector_store()  # 增量同步新文档
    else:
        init_vector_store()


def search_similar(query: str, k: int = 3):
    """相似度检索：返回最相关的 k 段诈骗剧本"""
    global _vector_store
    ensure_vector_store()

    docs = _vector_store.similarity_search(query, k=k)
    return [d.page_content for d in docs]
