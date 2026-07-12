"""bge-m3 hybrid embeddings — one model, dense + sparse (lexical) vectors."""
from . import config

_model = None


def get_model():
    global _model
    if _model is None:
        from FlagEmbedding import BGEM3FlagModel

        _model = BGEM3FlagModel(config.DENSE_MODEL_NAME, use_fp16=config.BGE_USE_FP16)
    return _model


def embed_texts(texts, batch_size=None):
    """Returns (dense_vecs, sparse_weights) — dense_vecs: list[list[float]] (1024-dim),
    sparse_weights: list[dict[int, float]] (token_id -> lexical weight)."""
    if not texts:
        return [], []

    model = get_model()
    output = model.encode(
        texts,
        batch_size=batch_size or config.INGEST_BATCH,
        max_length=8192,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    dense = [vec.tolist() for vec in output["dense_vecs"]]
    sparse = [{int(k): float(v) for k, v in weights.items()} for weights in output["lexical_weights"]]
    return dense, sparse


def embed_query(text):
    dense, sparse = embed_texts([text], batch_size=1)
    return dense[0], sparse[0]
