"""
rag_engine — a self-contained, cluster-routed RAG pipeline with an LRU/LFU
semantic cache.

Design goals:
  * Cluster the document embeddings (K-means). At query time, route the query to
    its nearest cluster(s) and search ONLY those — like FAISS IVF, but inspectable.
  * A cluster-partitioned semantic cache so repeated / similar questions skip both
    the vector search and the (expensive) LLM call. Eviction is LRU or LFU.
  * Everything pluggable: the embedder and the LLM are interfaces, so the same
    pipeline runs offline (TF-IDF + stub LLM) or in production
    (SentenceTransformers + Groq / Grok / Ollama).
"""

from .pipeline import RagPipeline
from .config import RagConfig

__all__ = ["RagPipeline", "RagConfig"]
