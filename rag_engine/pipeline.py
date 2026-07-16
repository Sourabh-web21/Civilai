"""RagPipeline — orchestrates embed -> cluster-route -> cache -> retrieve -> LLM."""
import time
import numpy as np

from .config import RagConfig
from .embeddings import build_embedder
from .clustering import ClusteredIndex
from .cache import SemanticClusterCache
from .ingest import docs_to_chunks
from .llm import get_llm, SYSTEM


class RagPipeline:
    def __init__(self, config: RagConfig = None, embedder=None, llm=None):
        self.cfg = config or RagConfig()
        self.embedder = embedder or build_embedder(self.cfg)
        self.index = ClusteredIndex(self.cfg.n_clusters)
        self.cache = SemanticClusterCache(
            capacity=self.cfg.cache_capacity,
            threshold=self.cfg.cache_threshold,
            policy=self.cfg.cache_policy,
        )
        self.llm = llm or get_llm(self.cfg)
        self._built = False

    # ---- build ----
    def build(self, docs):
        """docs: list of {text, source}. Chunks, fits embedder, builds cluster index."""
        chunks = docs_to_chunks(docs, self.cfg.chunk_chars, self.cfg.chunk_overlap)
        texts = [c["text"] for c in chunks]
        self.embedder.fit(texts)
        vectors = self.embedder.encode(texts)
        self.index.build(vectors, chunks)
        self._built = True
        return self

    # ---- query ----
    def answer(self, query, use_cache=True):
        if not self._built:
            raise RuntimeError("Pipeline not built — call .build(docs) first")

        t0 = time.perf_counter()
        qvec = self.embedder.encode(query)
        cluster_ids, _ = self.index.route(qvec, self.cfg.nprobe)
        primary = cluster_ids[0]
        t_embed = time.perf_counter() - t0

        # --- semantic cache lookup (scans only the primary cluster bucket) ---
        if use_cache:
            entry, sim = self.cache.get(qvec, primary)
            if entry is not None:
                total = time.perf_counter() - t0
                return {
                    "query": query,
                    "answer": entry.answer,
                    "sources": entry.sources,
                    "cluster": primary,
                    "cache_hit": True,
                    "cache_similarity": round(sim, 3),
                    "timing_ms": {"total": _ms(total), "embed": _ms(t_embed)},
                    "llm": self.llm.name,
                    "llm_fallback": False,
                }

        # --- retrieve (cluster-routed) ---
        t1 = time.perf_counter()
        results, probed, scanned = self.index.search(qvec, self.cfg.top_k, self.cfg.nprobe)
        t_retrieve = time.perf_counter() - t1

        context = "\n\n".join(f"[{r['source']}] {r['text']}" for r in results)
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

        # --- generate ---
        # If the configured backend fails (no credits, network down, bad model),
        # fall back to the offline extractive stub so the user still gets a
        # document-grounded answer instead of an error.
        t2 = time.perf_counter()
        llm_used = self.llm.name
        llm_fallback = False
        try:
            answer = self.llm.generate(prompt, SYSTEM)
        except Exception as exc:
            from .llm import StubLLM
            answer = StubLLM().generate(prompt, SYSTEM)
            llm_used, llm_fallback = "stub", True
            self._last_llm_error = str(exc)
        t_gen = time.perf_counter() - t2

        sources = [{"source": r["source"], "score": round(r["score"], 3)} for r in results]
        total = time.perf_counter() - t0

        if use_cache:
            self.cache.put(query, qvec, answer, sources, primary)

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "cluster": primary,
            "clusters_probed": probed,
            "candidates_scanned": scanned,
            "corpus_size": self.index.stats()["n_vectors"],
            "cache_hit": False,
            "timing_ms": {
                "total": _ms(total),
                "embed": _ms(t_embed),
                "retrieve": _ms(t_retrieve),
                "generate": _ms(t_gen),
            },
            "llm": self.llm.name,
            "llm_fallback": llm_fallback,
        }

    # ---- introspection ----
    def info(self):
        return {
            "built": self._built,
            "embedder": self.embedder.name,
            "embed_dim": getattr(self.embedder, "dim", None),
            "llm": self.llm.name,
            "index": self.index.stats() if self._built else None,
            "cache": self.cache.stats(),
            "config": self.cfg.__dict__,
        }


def _ms(seconds):
    return round(seconds * 1000, 2)
