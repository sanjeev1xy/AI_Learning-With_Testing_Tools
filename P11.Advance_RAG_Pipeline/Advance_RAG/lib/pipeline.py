"""Orchestrates ingest (SSE-friendly generator) and chat (single-shot dict result)."""
from . import config, embed, fusion, groq_client, qdrant_store, rerank
from .chunking import build_docs, chunk_docs, load_table

_tokenizer = None


def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(config.DENSE_MODEL_NAME)
    return _tokenizer


def sparse_top_tokens(sparse_weights, top_n=5):
    tokenizer = get_tokenizer()
    top = sorted(sparse_weights.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return [{"token": tokenizer.decode([tid]).strip(), "weight": round(weight, 4)} for tid, weight in top]


def ingest_stream(file_path, text_cols, meta_cols):
    """Yields SSE-style dicts: {stage, status, data}."""
    yield {"stage": "read", "status": "start", "data": {}}
    df = load_table(file_path)
    columns = list(df.columns)
    dtypes = {c: str(df[c].dtype) for c in columns}
    sample_rows = df.head(5).fillna("").to_dict(orient="records")
    yield {
        "stage": "read",
        "status": "done",
        "data": {"row_count": len(df), "columns": columns, "dtypes": dtypes, "sample_rows": sample_rows},
    }

    yield {"stage": "build_docs", "status": "start", "data": {}}
    docs = build_docs(df, text_cols, meta_cols)
    yield {"stage": "build_docs", "status": "done", "data": {"doc_count": len(docs)}}

    yield {"stage": "chunk", "status": "start", "data": {}}
    chunks = chunk_docs(docs)
    lengths = [len(c["text"]) for c in chunks]
    histogram = {}
    for length in lengths:
        bucket = f"{(length // 200) * 200}-{(length // 200) * 200 + 199}"
        histogram[bucket] = histogram.get(bucket, 0) + 1
    yield {
        "stage": "chunk",
        "status": "done",
        "data": {
            "total_chunks": len(chunks),
            "avg_chars": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "min_chars": min(lengths) if lengths else 0,
            "max_chars": max(lengths) if lengths else 0,
            "histogram": histogram,
            "sample_chunks": [c["text"][:300] for c in chunks[:5]],
        },
    }

    yield {"stage": "embed", "status": "start", "data": {"total": len(chunks)}}
    dense_vecs, sparse_weights = [], []
    batch_size = config.INGEST_BATCH
    texts = [c["text"] for c in chunks]
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        d, s = embed.embed_texts(batch, batch_size=batch_size)
        dense_vecs.extend(d)
        sparse_weights.extend(s)
        yield {
            "stage": "embed",
            "status": "progress",
            "data": {"done": len(dense_vecs), "total": len(texts)},
        }

    preview = {
        "dense_preview": dense_vecs[0][:8] if dense_vecs else [],
        "sparse_preview": sparse_top_tokens(sparse_weights[0]) if sparse_weights else [],
        "dims": len(dense_vecs[0]) if dense_vecs else 0,
    }
    yield {"stage": "embed", "status": "done", "data": preview}

    yield {"stage": "index", "status": "start", "data": {}}
    dense_size = len(dense_vecs[0]) if dense_vecs else 1024
    qdrant_store.reset_collection(dense_size=dense_size)
    for i in range(0, len(chunks), batch_size):
        qdrant_store.upsert_chunks(
            chunks[i : i + batch_size],
            dense_vecs[i : i + batch_size],
            sparse_weights[i : i + batch_size],
            id_offset=i,
        )
    info = qdrant_store.collection_info()
    yield {
        "stage": "index",
        "status": "done",
        "data": {"collection": config.COLLECTION_NAME, "points_count": info["points_count"]},
    }


def chat(question, top_n=None, top_k=None):
    top_n = top_n or config.TOP_N_HYBRID
    top_k = top_k or config.TOP_K_RERANK

    mode = groq_client.detect_mode(question)
    rewrites = groq_client.rewrite_query(question)

    dense_agg, sparse_agg = {}, {}
    for variant in rewrites:
        dense_vec, sparse_vec = embed.embed_query(variant)
        for pid, score, payload in qdrant_store.search_dense(dense_vec, top_n):
            if pid not in dense_agg or score > dense_agg[pid][0]:
                dense_agg[pid] = (score, payload)
        for pid, score, payload in qdrant_store.search_sparse(sparse_vec, top_n):
            if pid not in sparse_agg or score > sparse_agg[pid][0]:
                sparse_agg[pid] = (score, payload)

    dense_results = sorted(
        [(pid, s, p) for pid, (s, p) in dense_agg.items()], key=lambda r: r[1], reverse=True
    )[:top_n]
    sparse_results = sorted(
        [(pid, s, p) for pid, (s, p) in sparse_agg.items()], key=lambda r: r[1], reverse=True
    )[:top_n]

    fused = fusion.rrf_fuse(dense_results, sparse_results)
    rerank_candidates = fused[: max(top_n, top_k * 3)]

    candidate_texts = [c["payload"].get("text", "") for c in rerank_candidates]
    scores = rerank.rerank(question, candidate_texts)
    for c, score in zip(rerank_candidates, scores):
        c["rerank_score"] = float(score)

    reranked = sorted(rerank_candidates, key=lambda c: c["rerank_score"], reverse=True)
    top_chunks = reranked[:top_k]

    final_chunks = [{"text": c["payload"].get("text", ""), "payload": c["payload"]} for c in top_chunks]
    answer, total_tokens = groq_client.generate_answer(question, final_chunks, mode=mode)

    return {
        "question": question,
        "mode": mode,
        "rewrites": rewrites,
        "dense_top": [{"id": pid, "score": round(s, 4), "text": p.get("text", "")[:200]} for pid, s, p in dense_results[:top_k]],
        "sparse_top": [{"id": pid, "score": round(s, 4), "text": p.get("text", "")[:200]} for pid, s, p in sparse_results[:top_k]],
        "rrf_top": [
            {"id": c["id"], "rrf_score": round(c["rrf_score"], 5), "dense_rank": c["dense_rank"], "sparse_rank": c["sparse_rank"], "text": c["payload"].get("text", "")[:200]}
            for c in fused[:top_k]
        ],
        "rerank_table": [
            {"id": c["id"], "rrf_score": round(c["rrf_score"], 5), "rerank_score": round(c["rerank_score"], 4), "text": c["payload"].get("text", "")[:200]}
            for c in reranked[:top_k]
        ],
        "chunks_used": [{"id": c["id"], "text": c["payload"].get("text", ""), "payload": c["payload"]} for c in top_chunks],
        "answer": answer,
        "total_tokens": total_tokens,
        "model": config.GROQ_MODEL,
    }
