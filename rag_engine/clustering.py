"""Cluster-routed vector index.

Same core idea as a FAISS IVF index: K-means partitions the vectors into
`n_clusters` buckets (the coarse quantizer). A query is routed to the `nprobe`
nearest centroids and we only score the vectors inside those buckets — so most
of the corpus is never touched. `search_full` is a brute-force baseline kept so
the demo can measure the speedup.
"""
import numpy as np


class ClusteredIndex:
    def __init__(self, n_clusters: int = 8, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.vectors = None          # (N, D) L2-normalized
        self.payloads = []           # list of dicts, aligned with vectors
        self.labels = None           # (N,) cluster id per vector
        self.centroids = None        # (C, D) L2-normalized
        self.members = {}            # cluster_id -> np.array of row indices

    def build(self, vectors: np.ndarray, payloads: list):
        from sklearn.cluster import KMeans

        self.vectors = np.asarray(vectors, dtype=np.float32)
        self.payloads = list(payloads)
        n = len(self.vectors)
        c = max(1, min(self.n_clusters, n))
        self.n_clusters = c

        if c == 1:
            self.labels = np.zeros(n, dtype=int)
            self.centroids = _normalize(self.vectors.mean(axis=0, keepdims=True))
        else:
            km = KMeans(n_clusters=c, random_state=self.random_state, n_init=10)
            self.labels = km.fit_predict(self.vectors)
            # Re-normalize centroids so cosine == dot for centroid routing too.
            self.centroids = _normalize(km.cluster_centers_)

        self.members = {
            cid: np.where(self.labels == cid)[0] for cid in range(self.n_clusters)
        }
        return self

    # ---- routing ----
    def route(self, qvec: np.ndarray, nprobe: int = 2):
        """Return the ids of the `nprobe` nearest clusters for a query vector."""
        q = _normalize(qvec)[0]
        sims = self.centroids @ q                      # cosine to each centroid
        nprobe = max(1, min(nprobe, self.n_clusters))
        return np.argsort(-sims)[:nprobe].tolist(), sims

    # ---- search ----
    def search(self, qvec: np.ndarray, k: int = 4, nprobe: int = 2):
        """Cluster-routed search: only score vectors in the probed clusters."""
        q = _normalize(qvec)[0]
        cluster_ids, _ = self.route(qvec, nprobe)
        cand = np.concatenate([self.members[c] for c in cluster_ids]) if cluster_ids else np.array([], int)
        if cand.size == 0:
            return [], cluster_ids, 0
        sims = self.vectors[cand] @ q
        order = np.argsort(-sims)[:k]
        hits = [(int(cand[i]), float(sims[i])) for i in order]
        results = [{**self.payloads[idx], "score": score} for idx, score in hits]
        return results, cluster_ids, int(cand.size)

    def search_full(self, qvec: np.ndarray, k: int = 4):
        """Brute-force baseline over the entire corpus (for benchmarking)."""
        q = _normalize(qvec)[0]
        sims = self.vectors @ q
        order = np.argsort(-sims)[:k]
        return [{**self.payloads[i], "score": float(sims[i])} for i in order]

    def stats(self):
        sizes = {cid: int(len(m)) for cid, m in self.members.items()}
        return {
            "n_vectors": 0 if self.vectors is None else int(len(self.vectors)),
            "n_clusters": self.n_clusters,
            "cluster_sizes": sizes,
        }


def _normalize(mat: np.ndarray) -> np.ndarray:
    mat = np.asarray(mat, dtype=np.float32)
    if mat.ndim == 1:
        mat = mat[None, :]
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms
