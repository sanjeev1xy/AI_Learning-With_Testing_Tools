import os
import re
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = str(BASE_DIR / "backend" / "chroma_db")
COLLECTION_NAME = "test_plan_docs"

EMBED_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
GROQ_MODEL = "openai/gpt-oss-120b"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 4

_embedder = None
_chroma_client = None
_groq_client = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME, trust_remote_code=True)
    return _embedder


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma_client


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Copy backend/.env.example to backend/.env and add your key."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def find_source_pdf() -> Path:
    pdf_files = sorted(DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No .pdf file found in {DATA_DIR}")
    return pdf_files[0]


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}".strip() if tail else para
        else:
            current = para

        while len(current) > chunk_size:
            chunks.append(current[:chunk_size])
            current = current[chunk_size - overlap:]

    if current:
        chunks.append(current)

    return chunks


def ingest() -> dict:
    source_path = find_source_pdf()
    full_text = read_pdf(source_path)
    if not full_text.strip():
        raise ValueError(f"No extractable text found in {source_path.name}")

    chunks = chunk_text(full_text)

    embedder = get_embedder()
    prefixed = [f"search_document: {c}" for c in chunks]
    embeddings = embedder.encode(prefixed, normalize_embeddings=True).tolist()

    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    metadatas = [
        {"chunk_index": i, "char_count": len(c), "source": source_path.name}
        for i, c in enumerate(chunks)
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    return {
        "source_file": source_path.name,
        "total_characters": len(full_text),
        "num_chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embedding_model": EMBED_MODEL_NAME,
        "chunks_preview": [
            {"id": ids[i], "preview": chunks[i][:220], "char_count": len(chunks[i])}
            for i in range(len(chunks))
        ],
    }


def status() -> dict:
    client = get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
    except Exception:
        count = 0
    return {"ingested": count > 0, "num_chunks": count}


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    client = get_chroma_client()
    collection = client.get_collection(COLLECTION_NAME)

    embedder = get_embedder()
    query_embedding = embedder.encode(
        [f"search_query: {question}"], normalize_embeddings=True
    ).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    retrieved = []
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    for i in range(len(docs)):
        similarity = 1 - distances[i]
        retrieved.append(
            {
                "id": ids[i],
                "text": docs[i],
                "metadata": metadatas[i],
                "similarity": round(similarity, 4),
            }
        )
    return retrieved


def generate_answer(question: str, retrieved_chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Chunk {c['metadata']['chunk_index']}]\n{c['text']}" for c in retrieved_chunks
    )

    system_prompt = (
        "You are a helpful assistant answering questions about a QA Test Plan "
        "document. Answer ONLY using the provided context chunks. If the answer is "
        "not in the context, say you don't have enough information. Reference chunk "
        "numbers when relevant."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    client = get_groq_client()
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    return completion.choices[0].message.content


def query(question: str, top_k: int = TOP_K) -> dict:
    retrieved_chunks = retrieve(question, top_k=top_k)
    answer = generate_answer(question, retrieved_chunks)
    return {"question": question, "retrieved_chunks": retrieved_chunks, "answer": answer}
