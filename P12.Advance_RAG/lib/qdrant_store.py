"""Embedded Qdrant (local file store, no Docker) with a native dense + sparse hybrid collection."""
from qdrant_client import QdrantClient, models

from . import config

_client = None


def get_client():
    global _client
    if _client is None:
        if config.QDRANT_URL:
            _client = QdrantClient(url=config.QDRANT_URL)
        else:
            _client = QdrantClient(path=config.QDRANT_PATH)
    return _client


def reset_collection(dense_size=1024):
    client = get_client()
    if client.collection_exists(config.COLLECTION_NAME):
        client.delete_collection(config.COLLECTION_NAME)

    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config={"dense": models.VectorParams(size=dense_size, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams()},
    )


def collection_exists():
    return get_client().collection_exists(config.COLLECTION_NAME)


def collection_info():
    client = get_client()
    if not client.collection_exists(config.COLLECTION_NAME):
        return {"exists": False, "points_count": 0}
    info = client.get_collection(config.COLLECTION_NAME)
    return {"exists": True, "points_count": info.points_count}


def upsert_chunks(chunks, dense_vecs, sparse_weights, id_offset=0):
    client = get_client()
    points = []
    for i, (chunk, dense, sparse) in enumerate(zip(chunks, dense_vecs, sparse_weights)):
        indices = list(sparse.keys())
        values = list(sparse.values())
        points.append(
            models.PointStruct(
                id=id_offset + i,
                vector={
                    "dense": dense,
                    "sparse": models.SparseVector(indices=indices, values=values),
                },
                payload={"text": chunk["text"], **chunk["metadata"]},
            )
        )
    client.upsert(collection_name=config.COLLECTION_NAME, points=points)


def search_dense(dense_vec, top_n, query_filter=None):
    client = get_client()
    result = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=dense_vec,
        using="dense",
        limit=top_n,
        query_filter=query_filter,
        with_payload=True,
    )
    return [(p.id, p.score, p.payload) for p in result.points]


def search_sparse(sparse_weights, top_n, query_filter=None):
    client = get_client()
    indices = list(sparse_weights.keys())
    values = list(sparse_weights.values())
    if not indices:
        return []
    result = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=models.SparseVector(indices=indices, values=values),
        using="sparse",
        limit=top_n,
        query_filter=query_filter,
        with_payload=True,
    )
    return [(p.id, p.score, p.payload) for p in result.points]


def get_points_by_ids(ids):
    client = get_client()
    points = client.retrieve(collection_name=config.COLLECTION_NAME, ids=ids, with_payload=True)
    return {p.id: p.payload for p in points}


def scroll_chunks(limit=50, offset=None, search_text=None, filters=None):
    client = get_client()
    query_filter = None
    conditions = []
    if filters:
        for key, value in filters.items():
            if value:
                conditions.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
    if conditions:
        query_filter = models.Filter(must=conditions)

    points, next_offset = client.scroll(
        collection_name=config.COLLECTION_NAME,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=True,
        scroll_filter=query_filter,
    )

    results = []
    for p in points:
        dense = (p.vector or {}).get("dense", [])
        sparse = (p.vector or {}).get("sparse")
        sparse_preview = []
        if sparse is not None:
            pairs = sorted(zip(sparse.indices, sparse.values), key=lambda kv: kv[1], reverse=True)[:5]
            sparse_preview = [{"token_id": idx, "weight": round(val, 4)} for idx, val in pairs]
        results.append(
            {
                "id": p.id,
                "payload": p.payload,
                "dense_preview": [round(v, 4) for v in dense[:8]],
                "sparse_preview": sparse_preview,
            }
        )

    if search_text:
        needle = search_text.lower()
        results = [r for r in results if needle in str(r["payload"].get("text", "")).lower()]

    return results, next_offset
