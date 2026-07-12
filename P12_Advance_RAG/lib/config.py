import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Tunables ---
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 150))
TOP_N_HYBRID = int(os.environ.get("TOP_N_HYBRID", 20))
TOP_K_RERANK = int(os.environ.get("TOP_K_RERANK", 4))
RRF_K = int(os.environ.get("RRF_K", 60))
REWRITE_ENABLED = os.environ.get("REWRITE_ENABLED", "true").lower() != "false"
BGE_USE_FP16 = os.environ.get("BGE_USE_FP16", "1") == "1"
INGEST_BATCH = int(os.environ.get("INGEST_BATCH", 16))
PORT = int(os.environ.get("PORT", 5050))

# --- Services ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-120b"

QDRANT_URL = os.environ.get("QDRANT_URL")  # if set, connect to a real Qdrant server
QDRANT_PATH = str(BASE_DIR / "qdrant_data")  # embedded (file-backed) mode otherwise
COLLECTION_NAME = "vwo_test_cases"

DENSE_MODEL_NAME = "BAAI/bge-m3"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

DATA_DIR = BASE_DIR / "data"
TESTCASE_DIR = BASE_DIR / "testcase"
DEFAULT_CSV = TESTCASE_DIR / "test_cases.csv"
