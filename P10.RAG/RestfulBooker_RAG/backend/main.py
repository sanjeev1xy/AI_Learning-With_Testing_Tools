from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag_pipeline

app = FastAPI(title="RAG Explorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    top_k: int = 4


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def get_status():
    return rag_pipeline.status()


@app.post("/api/ingest")
def ingest():
    try:
        return rag_pipeline.ingest()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def run_query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")
    try:
        current_status = rag_pipeline.status()
        if not current_status["ingested"]:
            raise HTTPException(
                status_code=400, detail="No documents ingested yet. Run ingestion first."
            )
        return rag_pipeline.query(req.question, top_k=req.top_k)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
