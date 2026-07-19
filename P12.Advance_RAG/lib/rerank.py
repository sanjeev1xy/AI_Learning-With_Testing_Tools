"""bge-reranker-v2-m3 cross-encoder — re-scores (query, chunk) pairs directly."""
from . import config

_reranker = None


def get_reranker():
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker

        _reranker = FlagReranker(config.RERANKER_MODEL_NAME, use_fp16=config.BGE_USE_FP16)
    return _reranker


def rerank(query, candidate_texts):
    """Returns a list of scores (higher = more relevant), same order as candidate_texts."""
    if not candidate_texts:
        return []

    reranker = get_reranker()
    pairs = [[query, text] for text in candidate_texts]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    return list(scores)
