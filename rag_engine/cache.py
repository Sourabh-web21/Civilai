"""Cluster-partitioned semantic cache with LRU / LFU eviction.

Why this is fast:
  * Every cached answer is filed under the cluster its query routed to.
  * A lookup only scans entries in the SAME cluster bucket (a small slice of the
    cache), not the whole cache — so cache hits get quicker as the cache grows.
  * A "hit" is semantic: cosine similarity to a stored query >= threshold, so
    "What is the forest clearance status?" reuses the answer for
    "forest clearance status?" without another LLM call.

Eviction:
  * lru  -> evict the entry whose last access is oldest.
  * lfu  -> evict the entry with the fewest hits (ties broken by oldest access).
A single monotonic logical clock orders accesses (no wall-clock dependency).
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class CacheEntry:
    query: str
    vector: np.ndarray
    answer: str
    sources: list
    cluster: int
    freq: int = 1            # for LFU
    last_used: int = 0       # logical clock for LRU
    created: int = 0


class SemanticClusterCache:
    def __init__(self, capacity=128, threshold=0.92, policy="lru"):
        self.capacity = capacity
        self.threshold = threshold
        self.policy = policy.lower()
        self._buckets = {}       # cluster_id -> list[CacheEntry]
        self._size = 0
        self._clock = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _tick(self):
        self._clock += 1
        return self._clock

    def get(self, qvec: np.ndarray, cluster: int):
        """Return (entry, similarity) on a semantic hit, else (None, best_sim)."""
        bucket = self._buckets.get(cluster, [])
        if not bucket:
            self.misses += 1
            return None, 0.0
        q = _unit(qvec)
        sims = np.array([float(e.vector @ q) for e in bucket])
        i = int(np.argmax(sims))
        best = float(sims[i])
        if best >= self.threshold:
            entry = bucket[i]
            entry.freq += 1
            entry.last_used = self._tick()
            self.hits += 1
            return entry, best
        self.misses += 1
        return None, best

    def put(self, query, qvec, answer, sources, cluster):
        entry = CacheEntry(
            query=query,
            vector=_unit(qvec),
            answer=answer,
            sources=sources,
            cluster=cluster,
            last_used=self._tick(),
            created=self._clock,
        )
        self._buckets.setdefault(cluster, []).append(entry)
        self._size += 1
        if self._size > self.capacity:
            self._evict()
        return entry

    def _evict(self):
        """Drop one entry across all buckets according to the policy."""
        victim = None       # (cluster_id, index_in_bucket, entry)
        for cid, bucket in self._buckets.items():
            for idx, e in enumerate(bucket):
                if victim is None:
                    victim = (cid, idx, e)
                    continue
                _, _, best = victim
                if self.policy == "lfu":
                    # fewest hits; break ties by older last_used
                    if (e.freq, e.last_used) < (best.freq, best.last_used):
                        victim = (cid, idx, e)
                else:  # lru
                    if e.last_used < best.last_used:
                        victim = (cid, idx, e)
        if victim is not None:
            cid, idx, _ = victim
            self._buckets[cid].pop(idx)
            self._size -= 1
            self.evictions += 1

    def stats(self):
        total = self.hits + self.misses
        return {
            "policy": self.policy,
            "size": self._size,
            "capacity": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
            "buckets": {c: len(b) for c, b in self._buckets.items() if b},
        }

    def clear(self):
        self._buckets.clear()
        self._size = 0


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).ravel()
    n = np.linalg.norm(v)
    return v / n if n else v
