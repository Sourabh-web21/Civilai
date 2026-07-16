"""Central, env-overridable configuration for the RAG engine."""
from dataclasses import dataclass
import os


def _load_dotenv_once():
    """Populate os.environ from the project-root .env so os.getenv works whether
    the engine runs under Django (python-decouple doesn't export to os.environ)
    or standalone. Real environment variables always take precedence. No deps."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


_load_dotenv_once()


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class RagConfig:
    # --- embedding ---
    embedder: str = os.getenv("RAG_EMBEDDER", "tfidf")          # "tfidf" | "sentence-transformers"
    embed_dim: int = _int("RAG_EMBED_DIM", 128)                 # SVD target dim for tfidf
    st_model: str = os.getenv("RAG_ST_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # --- clustering / retrieval ---
    n_clusters: int = _int("RAG_N_CLUSTERS", 8)                 # number of embedding clusters
    nprobe: int = _int("RAG_NPROBE", 2)                         # how many nearest clusters to probe
    top_k: int = _int("RAG_TOP_K", 4)                           # chunks fed to the LLM

    # --- semantic cache ---
    cache_policy: str = os.getenv("RAG_CACHE_POLICY", "lru")    # "lru" | "lfu"
    cache_capacity: int = _int("RAG_CACHE_CAPACITY", 128)       # max cached answers (global)
    cache_threshold: float = _float("RAG_CACHE_THRESHOLD", 0.92)  # cosine sim to count as a hit

    # --- llm backend ---
    llm: str = os.getenv("RAG_LLM", "auto")                     # "auto"|"stub"|"ollama"|"groq"|"grok"

    # --- chunking ---
    chunk_chars: int = _int("RAG_CHUNK_CHARS", 600)
    chunk_overlap: int = _int("RAG_CHUNK_OVERLAP", 80)
