import json
import os
import traceback

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

from lib import config, qdrant_store
from lib.pipeline import chat, ingest_stream

app = Flask(__name__)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")


@app.route("/api/upload", methods=["POST"])
def api_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"detail": "No file provided"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"detail": "Only .csv, .xlsx, .xls are supported"}), 400

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.DATA_DIR / filename
    file.save(dest)

    import pandas as pd

    df = pd.read_excel(dest) if ext in (".xlsx", ".xls") else pd.read_csv(dest)
    return jsonify(
        {
            "filename": filename,
            "row_count": len(df),
            "columns": list(df.columns),
            "dtypes": {c: str(df[c].dtype) for c in df.columns},
            "sample_rows": df.head(5).fillna("").to_dict(orient="records"),
        }
    )


@app.route("/ingest")
def ingest_page():
    return render_template("ingest.html")


@app.route("/api/ingest", methods=["GET"])
def api_ingest_stream():
    filename = request.args.get("filename")
    text_cols = request.args.get("text_cols", "title,steps,expected,tags").split(",")
    meta_cols = request.args.get("meta_cols", "id,jira_id,priority,module").split(",")

    path = config.DATA_DIR / filename if filename else config.DEFAULT_CSV

    def generate():
        try:
            for event in ingest_stream(path, text_cols, meta_cols):
                yield f"data: {json.dumps(event)}\n\n"
            yield f"data: {json.dumps({'stage': 'complete', 'status': 'done', 'data': {}})}\n\n"
        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'stage': 'error', 'status': 'error', 'data': {'message': str(e)}})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/chunks")
def chunks_page():
    return render_template("chunks.html")


@app.route("/api/chunks", methods=["GET"])
def api_chunks():
    limit = int(request.args.get("limit", 50))
    offset = request.args.get("offset")
    offset = int(offset) if offset else None
    search_text = request.args.get("q") or None
    filters = {
        "priority": request.args.get("priority") or None,
        "module": request.args.get("module") or None,
        "jira_id": request.args.get("jira_id") or None,
    }

    if not qdrant_store.collection_exists():
        return jsonify({"results": [], "next_offset": None, "total": 0})

    results, next_offset = qdrant_store.scroll_chunks(limit, offset, search_text, filters)
    info = qdrant_store.collection_info()
    return jsonify({"results": results, "next_offset": next_offset, "total": info["points_count"]})


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.get_json(force=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"detail": "Question must not be empty"}), 400

    if not qdrant_store.collection_exists():
        return jsonify({"detail": "No data ingested yet. Run ingestion first."}), 400

    try:
        result = chat(question)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"detail": str(e)}), 500


@app.route("/api/status")
def api_status():
    info = qdrant_store.collection_info()
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=config.PORT, debug=True, threaded=True)
