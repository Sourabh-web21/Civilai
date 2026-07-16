"""Pluggable embedders. All return L2-normalized float32 vectors so cosine
similarity reduces to a dot product everywhere downstream."""
from abc import ABC, abstractmethod
import numpy as np


def l2_normalize(mat: np.ndarray) -> np.ndarray:
    mat = np.asarray(mat, dtype=np.float32)
    if mat.ndim == 1:
        mat = mat[None, :]
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


class Embedder(ABC):
    """Embedder interface. `fit` is optional (trainable embedders use it)."""
    dim: int = 0

    def fit(self, texts):  # default: nothing to learn
        return self

    @abstractmethod
    def encode(self, texts) -> np.ndarray:
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class TfidfEmbedder(Embedder):
    """Lightweight, dependency-cheap embedder: TF-IDF -> TruncatedSVD (LSA) ->
    L2-normalize. Runs anywhere numpy + scikit-learn are installed (no PyTorch).
    Good enough to demonstrate clustering, routing and caching end-to-end."""

    def __init__(self, dim: int = 128):
        self.dim = dim
        self._vectorizer = None
        self._svd = None

    def fit(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        texts = list(texts)
        self._vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), min_df=1, sublinear_tf=True
        )
        tfidf = self._vectorizer.fit_transform(texts)
        # SVD components can't exceed min(n_features, n_docs) - 1
        max_comp = max(2, min(self.dim, tfidf.shape[1] - 1, tfidf.shape[0] - 1))
        self._svd = TruncatedSVD(n_components=max_comp, random_state=42)
        self._svd.fit(tfidf)
        self.dim = max_comp
        return self

    def encode(self, texts) -> np.ndarray:
        if self._vectorizer is None or self._svd is None:
            raise RuntimeError("TfidfEmbedder must be .fit() on the corpus first")
        if isinstance(texts, str):
            texts = [texts]
        tfidf = self._vectorizer.transform(list(texts))
        dense = self._svd.transform(tfidf)
        return l2_normalize(dense)


class SentenceTransformerEmbedder(Embedder):
    """Production embedder. Lazy-imports sentence_transformers (needs torch)."""

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _ensure(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            # Method was renamed across sentence-transformers versions.
            get_dim = (getattr(self._model, "get_embedding_dimension", None)
                       or self._model.get_sentence_embedding_dimension)
            self.dim = get_dim()

    def encode(self, texts) -> np.ndarray:
        self._ensure()
        if isinstance(texts, str):
            texts = [texts]
        vecs = self._model.encode(list(texts), normalize_embeddings=False)
        return l2_normalize(np.asarray(vecs, dtype=np.float32))


def build_embedder(cfg) -> Embedder:
    if cfg.embedder == "sentence-transformers":
        return SentenceTransformerEmbedder(cfg.st_model)
    return TfidfEmbedder(cfg.embed_dim)
