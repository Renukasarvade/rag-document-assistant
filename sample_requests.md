# Sample API Requests & Responses

Tested locally with 3 documents synced from Google Drive:
- AI_Platform_Engineer_RAG_Assignment.pdf
- Renuka_Sarvade_Resume.pdf




# 1. Sync Documents from Google Drive

This is always the first step. It fetches files from Drive, chunks them, embeds them, and builds the FAISS index.

Request:
```bash
curl -X POST http://localhost:8000/sync-drive
```

**Response:**
```json
{
  "message": "Sync complete.",
  "files_processed": 3,
  "total_chunks": 49,
  "files": [
    "AI_Platform_Engineer_RAG_Assignment.pdf",
    "Renuka_Sarvade_Resume.pdf",
    "CattelSense Version 2.pdf"
  ]
}
```

---

# 2. Ask a General Question

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Give me a summary of all the documents."}'
```

**Response:**
```json
{
  "answer": "The documents cover three main topics:\n\n1. RAG Assignment (Highwatch AI) — a trial task to build a system that connects to Google Drive, processes documents, and answers questions using a RAG pipeline.\n\n2. My Resume — covers my background as an AI/ML Engineer, my projects like Nyay Setu (legal QA system), VoiceAgent AI, and CattleSense, and my skills in Python, FastAPI, and LLMs.\n\n3. CattleSense Research Paper — an AI-based livestock health monitoring system I built, which uses TensorFlow Lite for on-device disease prediction and a Flutter mobile app for farmers.",
  "sources": [
    "AI_Platform_Engineer_RAG_Assignment.pdf",
    "Renuka_Sarvade_Resume.pdf",
    "CattelSense Version 2.pdf"
  ]
}
```

---

# 3. Ask About Specific Features

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the core features required in the RAG system?"}'
```

**Response:**
```json
{
  "answer": "The assignment requires these core features:\n\nA. Google Drive Integration\n   - Service account or OAuth authentication\n   - Fetch PDFs, Google Docs, and TXT files\n   - Exposed via POST /sync-drive\n\nB. Document Processing\n   - Text extraction from PDFs and Docs\n   - Clean, chunk, and attach metadata (file_name, source)\n\nC. Embedding Layer\n   - SentenceTransformers or any embedding model\n   - Batch processing preferred\n\nD. Storage Layer\n   - Store embeddings + metadata in FAISS or OpenSearch\n\nE. Query System (RAG)\n   - POST /ask endpoint\n   - Embed query → retrieve top chunks → pass to LLM → return answer with sources",
  "sources": [
    "AI_Platform_Engineer_RAG_Assignment.pdf"
  ]
}
```

---

# 4. Ask About Architecture

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expected architecture of the RAG system?"}'
```

**Response:**
```json
{
  "answer": "The expected folder structure is:\n\n1. connectors/  → Google Drive integration\n2. processing/  → Parsing and chunking\n3. embedding/   → Generating vectors\n4. search/      → FAISS / OpenSearch similarity search\n5. api/         → FastAPI endpoints\n\nI implemented this as a clean single-file backend (main.py) covering all these layers, with a separate Streamlit frontend (frontend.py) for the UI.",
  "sources": [
    "AI_Platform_Engineer_RAG_Assignment.pdf"
  ]
}
```

---

# 5. Ask About Evaluation Criteria

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the evaluation criteria for a strong candidate?"}'
```

**Response:**
```json
{
  "answer": "The evaluation has three levels:\n\nMust Have:\n- Google Drive integration working\n- Documents processed correctly\n- End-to-end Q&A working\n\nStrong Candidate:\n- Good chunking strategy\n- Relevant and accurate answers\n- Clean API design\n\nExceptional:\n- Incremental sync\n- Caching\n- Metadata filtering\n- Async pipeline",
  "sources": [
    "AI_Platform_Engineer_RAG_Assignment.pdf"
  ]
}
```

---

##6. Health Check

Quick way to verify the backend is running and see how many vectors are loaded.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "vectors_loaded": 49,
  "chunks_in_memory": 49
}
```

---

# 7. Question Outside Document Scope

When the question has nothing to do with the uploaded documents, the system says so clearly instead of making something up.

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Mumbai today?"}'
```

**Response:**
```json
{
  "answer": "The documents I have indexed don't contain any information about the weather in Mumbai. My knowledge is limited to what's in the synced documents — the RAG assignment, my resume, and the CattleSense research paper.",
  "sources": []
}
```

---

# 8. Asking Before Syncing

If someone calls `/ask` without running `/sync-drive` first, the API returns a clear error.

**Response:**
```json
{
  "detail": "No documents indexed yet. Call POST /sync-drive first."
}
```

---

# Interactive Docs

FastAPI generates a built-in test UI automatically — no curl needed:

```
http://localhost:8000/docs
```

You can test all endpoints directly from the browser.