from . import config


def rrf_fuse(dense_results, sparse_results, k=config.RRF_K):
    """dense_results/sparse_results: list[(id, score, payload)], best-first.
    Returns list[{id, payload, rrf_score, dense_rank, sparse_rank}], best-first."""
    payloads = {}
    dense_rank = {}
    for rank, (pid, _score, payload) in enumerate(dense_results, start=1):
        dense_rank[pid] = rank
        payloads[pid] = payload

    sparse_rank = {}
    for rank, (pid, _score, payload) in enumerate(sparse_results, start=1):
        sparse_rank[pid] = rank
        payloads[pid] = payload

    all_ids = set(dense_rank) | set(sparse_rank)
    fused = []
    for pid in all_ids:
        score = 0.0
        if pid in dense_rank:
            score += 1.0 / (k + dense_rank[pid])
        if pid in sparse_rank:
            score += 1.0 / (k + sparse_rank[pid])
        fused.append(
            {
                "id": pid,
                "payload": payloads[pid],
                "rrf_score": score,
                "dense_rank": dense_rank.get(pid),
                "sparse_rank": sparse_rank.get(pid),
            }
        )

    fused.sort(key=lambda r: r["rrf_score"], reverse=True)
    return fused
