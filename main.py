#!/usr/bin/env python3
"""
RAG System with Google Drive Integration
=========================================
Simple, clean RAG pipeline:
  1. Fetch files from Google Drive
  2. Extract text from PDF / Google Docs / TXT
  3. Chunk text into segments
  4. Generate embeddings (SentenceTransformers)
  5. Store in FAISS vector DB
  6. Answer questions using retrieved context + LLM (Groq)

APIs:
  POST /sync-drive  → fetch & process files from Google Drive
  POST /ask         → ask a question, get an answer with sources
"""

import os
import io
import json
import numpy as np
import faiss
import PyPDF2

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

# ─── Google Drive SDK ──────────────────────────────────────────────────────────
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

FAISS_INDEX_FILE = "faiss_index.bin"
METADATA_FILE    = "chunks_metadata.json"
DOWNLOAD_DIR     = "drive_downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════

_embedding_model = None
_faiss_index     = None
_chunks_metadata = []


def get_model():
    """
    Lazy-load the embedding model.
    Model is NOT loaded at startup — only when first needed.
    This lets the HTTP port open in ~1 second, fixing Render's
    "No open ports detected" error caused by slow startup.
    """
    global _embedding_model
    if _embedding_model is None:
        # Import here so the module-level import cost is deferred too
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model ...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model ready.")
    return _embedding_model


# ══════════════════════════════════════════════════════════════════════
# FAISS HELPERS
# ══════════════════════════════════════════════════════════════════════

def save_index(index, metadata):
    faiss.write_index(index, FAISS_INDEX_FILE)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Saved {index.ntotal} vectors + metadata.")


def load_index():
    if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(METADATA_FILE):
        index = faiss.read_index(FAISS_INDEX_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"Loaded {index.ntotal} vectors from disk.")
        return index, metadata
    return None, []


# ══════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE
# ══════════════════════════════════════════════════════════════════════

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    """
    Build Google Drive client.
    - Local dev: reads from GOOGLE_SERVICE_ACCOUNT_FILE (path to .json file)
    - Production/Docker: reads from GOOGLE_SERVICE_ACCOUNT_JSON (full JSON string)
    """
    key_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not key_json:
        # Fallback for local dev — read from file path
        key_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not key_file:
            raise ValueError(
                "Set either GOOGLE_SERVICE_ACCOUNT_JSON (full JSON string) "
                "or GOOGLE_SERVICE_ACCOUNT_FILE (path to .json file) in your .env"
            )
        if not os.path.exists(key_file):
            raise ValueError(f"Service account file not found: {key_file}")
        with open(key_file, "r") as f:
            key_json = f.read()

    try:
        key_data = json.loads(key_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in service account credentials")

    creds = service_account.Credentials.from_service_account_info(
        key_data,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def list_drive_files(service):
    mime_filter = " or ".join([
        "mimeType='application/pdf'",
        "mimeType='application/vnd.google-apps.document'",
        "mimeType='text/plain'",
    ])
    query = f"({mime_filter}) and trashed=false"
    if DRIVE_FOLDER_ID:
        query += f" and '{DRIVE_FOLDER_ID}' in parents"

    files, page_token = [], None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
            pageSize=100,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(files)} files on Google Drive.")
    return files


def download_file(service, file_info):
    mime    = file_info["mimeType"]
    file_id = file_info["id"]
    try:
        if mime == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
        else:
            request = service.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
    except Exception as e:
        print(f"  Could not download '{file_info['name']}': {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ══════════════════════════════════════════════════════════════════════

def extract_text(file_bytes, mime_type):
    if mime_type == "text/plain":
        return file_bytes.decode("utf-8", errors="ignore")
    text = ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"  PDF extraction error: {e}")
    return text


# ══════════════════════════════════════════════════════════════════════
# CHUNKING
# ══════════════════════════════════════════════════════════════════════

def chunk_text(text, chunk_size=150, overlap=30):
    """
    Split text into smaller, focused chunks.
    150 words per chunk = one specific topic per chunk.
    30-word overlap = context not lost at boundaries.
    Smaller chunks → much more precise FAISS matching.
    """
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end   = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


# ══════════════════════════════════════════════════════════════════════
# EMBEDDING + INDEXING
# ══════════════════════════════════════════════════════════════════════

def embed_and_index(chunks, file_name):
    model      = get_model()
    embeddings = model.encode(chunks, show_progress_bar=False, batch_size=32)
    metadata   = [{"text": c, "file_name": file_name, "source": "gdrive"} for c in chunks]
    return np.array(embeddings, dtype="float32"), metadata


def build_faiss_index(all_embeddings):
    dim   = all_embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(all_embeddings)
    return index


# ══════════════════════════════════════════════════════════════════════
# RETRIEVAL
# ══════════════════════════════════════════════════════════════════════

def retrieve(query, top_k=8):
    """
    Two-stage retrieval:
    Stage 1 — FAISS vector search: fetch top 20 candidates by semantic similarity.
    Stage 2 — Keyword re-ranking: boost chunks that also contain query words.
    This fixes cases where FAISS returns the wrong file because
    a resume chunk is semantically close but the assignment chunk
    is the actual correct answer.
    """
    global _faiss_index, _chunks_metadata
    if _faiss_index is None or not _chunks_metadata:
        return []

    model = get_model()
    q_emb = model.encode([query], show_progress_bar=False).astype("float32")

    # Stage 1: get top 20 from FAISS
    fetch_k = min(20, _faiss_index.ntotal)
    distances, indices = _faiss_index.search(q_emb, fetch_k)

    # Stage 2: re-rank with keyword bonus
    query_words = set(query.lower().split())
    candidates = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(_chunks_metadata):
            entry = _chunks_metadata[idx].copy()
            semantic_score = float(1 / (1 + dist))   # higher = better

            # Count how many query words appear in this chunk
            chunk_words = set(entry["text"].lower().split())
            keyword_hits = len(query_words & chunk_words)
            keyword_bonus = keyword_hits * 0.05       # small boost per keyword match

            entry["score"] = semantic_score + keyword_bonus
            candidates.append(entry)

    # Sort by combined score, return top_k
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


# ══════════════════════════════════════════════════════════════════════
# LLM ANSWER (Groq)
# ══════════════════════════════════════════════════════════════════════

# Groq models tried in order — all free-tier eligible
GROQ_MODEL_CHAIN = [
    "llama-3.3-70b-versatile",       # best quality, generous free limits
    "llama3-8b-8192",                 # fastest, lightest
    "mixtral-8x7b-32768",             # large context window fallback
    "gemma2-9b-it",                   # Google Gemma fallback
]


def _call_groq(model: str, messages: list):
    """Single Groq call. Returns (text, error_code).
    text is None on failure; error_code is None on success."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
        text = completion.choices[0].message.content
        return text.strip() if text else None, None
    except Exception as e:
        err_str = str(e)
        # Parse HTTP status from Groq exception message if present
        if "429" in err_str:
            return None, 429
        if "503" in err_str or "502" in err_str:
            return None, 503
        if "400" in err_str:
            return None, 400
        raise  # re-raise unexpected errors


def generate_answer(question, context_chunks):
    if not GROQ_API_KEY:
        return "[Groq API key not configured. Set GROQ_API_KEY in .env]"

    # Label each chunk with its source file so the LLM knows where info comes from
    context_parts = []
    for c in context_chunks:
        context_parts.append(f"[Source: {c['file_name']}]\n{c['text']}")
    context = "\n\n---\n\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful document assistant. "
                "Answer questions using ONLY the provided document context. "
                "Give detailed, well-structured answers. "
                "Use bullet points or numbered lists when listing multiple items. "
                "If the context contains partial information, explain what is available. "
                "If the answer is truly not in the context, say so clearly."
            ),
        },
        {
            "role": "user",
            "content": (
                "Use the document context below to answer the question in detail.\n"
                "Do NOT say 'based on the context' repeatedly — just answer directly.\n"
                "Structure your answer clearly. Be thorough and complete.\n\n"
                f"=== DOCUMENT CONTEXT ===\n{context}\n\n"
                f"=== QUESTION ===\n{question}\n\n"
                "=== DETAILED ANSWER ==="
            ),
        },
    ]

    # Build model list: primary from .env first, then fallbacks
    models_to_try = [GROQ_MODEL] if GROQ_MODEL else []
    for m in GROQ_MODEL_CHAIN:
        if m not in models_to_try:
            models_to_try.append(m)

    for model in models_to_try:
        print(f"Trying Groq model: {model}")
        try:
            text, code = _call_groq(model, messages)
            if text:
                print(f"  ✓ Success with model: {model}")
                return text
            if code in (429, 503, 502):
                print(f"  Model {model} rate-limited (HTTP {code}), trying next ...")
                continue
        except Exception as e:
            print(f"  Model {model} threw exception: {e}, trying next ...")
            continue

    return "[All Groq models are currently unavailable. Please wait a moment and try again.]"


# ══════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ══════════════════════════════════════════════════════════════════════

class AskRequest(BaseModel):
    query: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: only load the FAISS index from disk (fast, ~100ms).
    Do NOT load the embedding model here — that takes 10-30 seconds
    and causes Render to kill the app before the port is opened.
    The model will lazy-load on the first real request instead.
    """
    global _faiss_index, _chunks_metadata
    _faiss_index, _chunks_metadata = load_index()
    yield

app = FastAPI(title="RAG + Google Drive", version="1.0", lifespan=lifespan)


# ── POST /sync-drive ───────────────────────────────────────────────────────────
@app.post("/sync-drive")
def sync_drive():
    global _faiss_index, _chunks_metadata

    try:
        service = get_drive_service()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    files = list_drive_files(service)
    if not files:
        return {"message": "No supported files found on Google Drive.", "files_processed": 0}

    all_embeddings  = []
    all_metadata    = []
    processed_files = []

    for file_info in files:
        print(f"Processing: {file_info['name']}")
        file_bytes = download_file(service, file_info)
        if not file_bytes:
            continue

        mime           = file_info["mimeType"]
        effective_mime = "application/pdf" if mime == "application/vnd.google-apps.document" else mime
        text           = extract_text(file_bytes, effective_mime)
        if not text.strip():
            print(f"  No text extracted from '{file_info['name']}', skipping.")
            continue

        chunks = chunk_text(text)
        if not chunks:
            continue

        embeddings, metadata = embed_and_index(chunks, file_info["name"])
        all_embeddings.append(embeddings)
        all_metadata.extend(metadata)
        processed_files.append(file_info["name"])
        print(f"  -> {len(chunks)} chunks from '{file_info['name']}'")

    if not all_embeddings:
        return {"message": "No text could be extracted from any files.", "files_processed": 0}

    combined         = np.vstack(all_embeddings)
    _faiss_index     = build_faiss_index(combined)
    _chunks_metadata = all_metadata

    save_index(_faiss_index, _chunks_metadata)

    return {
        "message": "Sync complete.",
        "files_processed": len(processed_files),
        "total_chunks": len(all_metadata),
        "files": processed_files,
    }


# ── POST /ask ──────────────────────────────────────────────────────────────────
@app.post("/ask")
def ask(body: AskRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if _faiss_index is None or not _chunks_metadata:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet. Call POST /sync-drive first.",
        )

    top_chunks = retrieve(body.query, top_k=8)
    if not top_chunks:
        return {"answer": "No relevant information found in the indexed documents.", "sources": []}

    answer  = generate_answer(body.query, top_chunks)
    sources = list(dict.fromkeys(c["file_name"] for c in top_chunks))

    return {"answer": answer, "sources": sources}


# ── GET /health ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "vectors_loaded":   _faiss_index.ntotal if _faiss_index else 0,
        "chunks_in_memory": len(_chunks_metadata),
        "model_loaded":     _embedding_model is not None,
    }


# ── run directly ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)