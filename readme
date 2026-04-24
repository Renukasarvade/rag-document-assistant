#  DriveRAG — Ask Your Google Drive Documents

> **Built for:** Highwatch AI – AI Platform Engineer Trial Assignment  
> **What it does:** Connect your Google Drive → Upload documents → Ask questions → Get smart answers

---

##  What Is This Project?

Imagine you have 10 PDF files in Google Drive — company policies, SOPs, research papers.  
Instead of reading all of them manually, you just **ask a question** like:

> *"What is the refund policy?"*

And this system **reads the documents for you** and gives a **precise, detailed answer** with the **source file name**.

That's exactly what this system does. It's called **RAG** — Retrieval-Augmented Generation.

---

## Architecture — How It All Fits Together
   Data
[ Google Drive ]
        ↓
  Processing
[ Fetch ] → [ Extract ] → [ Chunk ]
        ↓
  Intelligence
[ Embeddings ] → [ FAISS Store ]
        ↓
  Query Flow
[ Question ] → [ Retrieve ] → [ LLM ]
        ↓
   Output
[ Answer + Sources ]



#  Workflow — Plain English

# When you click "- Sync Drive Now"

```
① System logs into Google Drive using service_account.json
② Finds all PDF / Google Docs / TXT files in your Drive
③ For each file:
    a. Downloads the file
    b. Extracts the text (PyPDF2 for PDFs)
    c. Splits text into 500-word chunks with 100-word overlap
    d. Converts each chunk into a vector (384 numbers) using AI model
④ Stores all vectors in FAISS (an in-memory search engine)
⑤ Saves everything to disk (faiss_index.bin + chunks_metadata.json)
```

### When you ask a question

```
① Your question is converted to a vector (same AI model)
② FAISS finds the 8 most similar vectors = most relevant text chunks
③ Those 8 chunks are sent to Groq LLM with the question
④ LLM reads the chunks and writes a detailed, structured answer
⑤ Answer + source file names are returned to the UI
```

---

## Project Structure

```
rag-project/
│
├── main.py                  ← Entire backend in one file
│                              (Drive sync + RAG pipeline + API)
│
├── frontend.py              ← Entire frontend in one file
│                              (Streamlit chat UI)
│
├── requirements.txt         ← Python packages list
│
├── .env                     ← Your API keys (YOU create this)
│
├── service_account.json     ← Google Drive key (YOU download this)
│
├── faiss_index.bin          ← Auto-created after first sync
│
└── chunks_metadata.json     ← Auto-created after first sync
```

---

##  Complete Setup Guide

### What You Need
- Python 3.10 or 3.11
- A Google account (free)
- A Groq account (free)

---

### STEP 1 — Create Your Project Folder

```bash
mkdir rag-project
cd rag-project
```

Put `main.py`, `frontend.py`, and `requirements.txt` in this folder.

---

### STEP 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` at the start of your terminal. That means it's active.

---

### STEP 3 — Install All Packages

```bash
pip install -r requirements.txt
pip install streamlit
```

Takes 3–5 minutes first time. Downloads FastAPI, FAISS, SentenceTransformers, Groq SDK, etc.

---

### STEP 4 — Get Your FREE Groq API Key

```
1. Go to:  https://console.groq.com
2. Sign up (takes 1 minute, completely free)
3. Click "API Keys" in the left menu
4. Click "Create API Key"
5. Copy the key  →  it starts with:  gsk_...
```

---

### STEP 5 — Set Up Google Drive Access

This is a one-time setup. Takes about 5 minutes.

#### 5a. Go to Google Cloud Console
```
https://console.cloud.google.com
```

#### 5b. Create a New Project
```
Top of page → click the project dropdown → "New Project"
Name: rag-project → Click "Create"
```

#### 5c. Enable Google Drive API
```
Left menu → "APIs & Services" → "Library"
Search: "Google Drive API"
Click it → Click "Enable"
```

#### 5d. Create a Service Account
```
Left menu → "APIs & Services" → "Credentials"
Click "+ Create Credentials" → "Service Account"
Name it:  rag-reader
Click "Create and Continue" → skip optional steps → "Done"
```

#### 5e. Download the JSON Key File
```
Click on the service account you just created
Go to the "Keys" tab
Click "Add Key" → "Create new key" → "JSON" → "Create"
```
A `.json` file will download automatically.  
**Rename it to `service_account.json`** and put it in your project folder.

#### 5f. Share Your Google Drive Folder With the Service Account
```
Open Google Drive in browser
Right-click the folder that has your PDFs → "Share"
In the email box, paste the service account email
  (looks like: rag-reader@rag-project-123456.iam.gserviceaccount.com)
  Find this email on the service account details page in Google Cloud Console
Set role to "Viewer" → Click "Send"
```

---

### STEP 6 — Create Your .env File

In your project folder, create a new file named `.env` (include the dot):

```
GROQ_API_KEY=gsk_your_actual_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
DRIVE_FOLDER_ID=
```

> Leave `DRIVE_FOLDER_ID` empty to scan your whole Drive.  
> To limit to one folder: open it in browser → copy the ID from the URL  
> Example: `drive.google.com/drive/folders/1AbCdEfGhIjK` → ID is `1AbCdEfGhIjK`

---

### STEP 7 — Run the Backend

In Terminal 1 (with venv active):

```bash
python main.py
```

Expected output:
```
Loading embedding model ...
Embedding model ready.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Keep this terminal open.**

---

### STEP 8 — Run the Frontend

In Terminal 2 (open a new terminal, activate venv):

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

streamlit run frontend.py
```

Browser auto-opens at: **http://localhost:8501**

---

### STEP 9 — Use the App

```
1. In the sidebar → Click " Sync Drive Now"
   Wait 30 seconds to a few minutes depending on file sizes
   You'll see: " Synced 3 files · 142 chunks"

2. Type your question in the text box (or click a suggestion)

3. Press "Ask →"

4. Read your answer and see which files it came from
```

---

##  API Reference

### POST /sync-drive
Connects to Google Drive, downloads files, processes them, builds the vector index.

```bash
curl -X POST http://localhost:8000/sync-drive
```

**Response:**
```json
{
  "message": "Sync complete.",
  "files_processed": 3,
  "total_chunks": 142,
  "files": ["policy.pdf", "handbook.pdf", "sop.txt"]
}
```

---

### POST /ask
Ask a question. Gets answered using the indexed documents.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our refund policy?"}'
```

**Response:**
```json
{
  "answer": "According to the policy document, the refund policy includes:\n1. Refunds accepted within 30 days of purchase\n2. Item must be in original condition\n3. Digital products are non-refundable\n4. Processing takes 5-7 business days",
  "sources": ["policy.pdf"]
}
```

---

### GET /health
Check if backend is alive and how many documents are loaded.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "vectors_loaded": 142,
  "chunks_in_memory": 142
}
```

---

###  Interactive Docs (No curl needed)
FastAPI auto-generates a visual test page:  
 **http://localhost:8000/docs**

---

##  Sample Test Case

**Scenario:** You uploaded `company_policy.pdf` to your Google Drive.

**Step 1 — Sync:**
```
POST /sync-drive
→ { "files_processed": 1, "total_chunks": 28 }
```

**Step 2 — Ask:**
```
POST /ask
{ "query": "What is the leave policy for new employees?" }
```

**Answer:**
```
New employees are entitled to the following leave benefits:

1. Casual Leave: 12 days per year (prorated in the joining year)
2. Sick Leave: 7 days per year
3. Earned Leave: Starts accruing after 6 months of continuous service

Important rules:
- Leave must be approved by the direct manager
- Apply at least 3 days in advance for planned leaves
- Emergency leaves can be applied within 24 hours

Sources: company_policy.pdf
```

---

##  Tech Stack

| Component | Tool | Why Chosen |
|---|---|---|
| Backend API | FastAPI | Fast, auto-generates docs at /docs |
| Frontend | Streamlit | Easy to build beautiful UI quickly |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) | Free, runs locally, very accurate |
| Vector Database | FAISS | No server needed, blazing fast search |
| LLM | Groq — llama-3.3-70b-versatile | Free tier, extremely fast, high quality |
| Drive Access | Google Service Account | Secure, no user login prompts |
| PDF Reading | PyPDF2 | Simple and reliable |

---

##  Troubleshooting

| Problem | Solution |
|---|---|
| `service_account.json not found` | File must be in same folder as main.py |
| `No files found on Drive` | Share the Drive folder with the service account email |
| Red dot "Backend offline" in UI | Run `python main.py` and keep that terminal open |
| Answers are too short | Already fixed: top_k=8, max_tokens=1024 |
| `GROQ_API_KEY not configured` | Check `.env` file — key should start with `gsk_` |
| Streamlit won't start | Make sure venv is activated and streamlit is installed |
| Sync takes too long | Normal for large files — first time downloads + embeds everything |

---

##  What This Demonstrates

| Assignment Requirement | Implementation |
|---|---|
| Google Drive Integration | `get_drive_service()` + service account auth |
| Fetch PDFs / Docs | `list_drive_files()` + `download_file()` |
| Extract Text | `extract_text()` using PyPDF2 |
| Chunking Strategy | 500-word chunks, 100-word overlap |
| Generate Embeddings | SentenceTransformers all-MiniLM-L6-v2 |
| Store in Vector DB | FAISS IndexFlatL2, persisted to disk |
| POST /sync-drive API | ✅ Implemented |
| POST /ask RAG API | ✅ Implemented with top-8 retrieval |
| Return answer + sources | ✅ `{"answer": "...", "sources": [...]}` |
| Clean architecture | Single backend file + single frontend file |