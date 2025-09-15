from __future__ import annotations

import threading
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model_lock = threading.Lock()
_cached_model: SentenceTransformer | None = None


def _load_model() -> SentenceTransformer:
    global _cached_model
    with _model_lock:
        if _cached_model is None:
            _cached_model = SentenceTransformer(_MODEL_NAME)
        return _cached_model


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Return embeddings for a batch of texts as a 2D numpy array.

    The function lazily loads the global model and ensures thread-safety.
    """
    model = _load_model()
    # Convert generator to list to avoid single-pass issues
    list_texts = list(texts)
    if not list_texts:
        return np.empty((0, 384), dtype=np.float32)
    embeddings = model.encode(list_texts, convert_to_numpy=True, normalize_embeddings=False)
    return embeddings.astype(np.float32)


def embed_single(text: str) -> List[float]:
    vec = embed_texts([text])
    return vec[0].astype(float).tolist()


