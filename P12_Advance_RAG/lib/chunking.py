import pandas as pd

from . import config


def load_table(path):
    path = str(path)
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    return pd.read_csv(path)


def build_docs(df, text_cols, meta_cols):
    """One row -> one doc: concatenated text + metadata payload."""
    docs = []
    for _, row in df.iterrows():
        parts = [f"{col}: {row[col]}" for col in text_cols if col in row and pd.notna(row[col])]
        text = "\n".join(parts)
        metadata = {col: (None if pd.isna(row[col]) else row[col]) for col in meta_cols if col in row}
        docs.append({"text": text, "metadata": metadata})
    return docs


def chunk_doc_text(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """1 row = 1 chunk if it fits; otherwise split with overlap."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def chunk_docs(docs, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """Returns a flat list of {text, metadata, chunk_index, row_index} chunks."""
    chunks = []
    for row_idx, doc in enumerate(docs):
        pieces = chunk_doc_text(doc["text"], chunk_size, overlap)
        for i, piece in enumerate(pieces):
            chunks.append(
                {
                    "text": piece,
                    "metadata": {**doc["metadata"], "row_index": row_idx, "chunk_index": i},
                }
            )
    return chunks
