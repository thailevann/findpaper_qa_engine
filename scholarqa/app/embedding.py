from __future__ import annotations

import threading
from typing import Iterable, List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model_lock = threading.Lock()
_cached_model: SentenceTransformer | None = None
_embedding_cache: Dict[str, np.ndarray] = {}  # Global cache for embeddings


def _load_model() -> SentenceTransformer:
    """Thread-safe lazy loading of SentenceTransformer model."""
    global _cached_model
    with _model_lock:
        if _cached_model is None:
            _cached_model = SentenceTransformer(_MODEL_NAME)
        return _cached_model


def embed_texts(texts: Iterable[str], batch_size: int = 64, use_cache: bool = True) -> np.ndarray:
    """
    Encode a batch of texts into embeddings with optional caching.

    Args:
        texts: Iterable of strings to encode.
        batch_size: Batch size for model.encode (tune for CPU/GPU).
        use_cache: Whether to use cached embeddings if available.

    Returns:
        2D numpy array of shape (len(texts), embedding_dim)
    """
    model = _load_model()
    texts_list = list(texts)
    if not texts_list:
        return np.empty((0, model.get_sentence_embedding_dimension()), dtype=np.float32)

    embeddings_list = []
    texts_to_encode = []
    indices_to_encode = []

    # Check cache
    for i, t in enumerate(texts_list):
        if use_cache and t in _embedding_cache:
            embeddings_list.append(_embedding_cache[t])
        else:
            embeddings_list.append(None)  # placeholder
            texts_to_encode.append(t)
            indices_to_encode.append(i)

    # Encode texts not in cache
    if texts_to_encode:
        new_embeddings = model.encode(
            texts_to_encode,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False
        ).astype(np.float32)

        for idx, t, emb in zip(indices_to_encode, texts_to_encode, new_embeddings):
            embeddings_list[idx] = emb
            if use_cache:
                _embedding_cache[t] = emb

    # Stack into 2D array
    return np.vstack(embeddings_list)


def embed_single(text: str, use_cache: bool = True) -> List[float]:
    """
    Encode a single text into a list of floats.
    """
    vec = embed_texts([text], use_cache=use_cache)
    return vec[0].tolist()