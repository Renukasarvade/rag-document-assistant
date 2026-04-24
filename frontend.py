import streamlit as st
import requests
import time

# ══════════════════════════════════════════════════════════════════════
# CONFIG — points to the FastAPI backend
# ══════════════════════════════════════════════════════════════════════
BACKEND_URL = "http://localhost:8000"   # change if your backend runs elsewhere

# ══════════════════════════════════════════════════════════════════════
# PAGE SETUP
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DriveRAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS  (black + dark-blue theme)
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:wght@400;500&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #050810;
    --surface:   #0d1220;
    --card:      #111827;
    --border:    #1e2d4a;
    --accent:    #3b82f6;
    --accent2:   #06b6d4;
    --green:     #10b981;
    --red:       #ef4444;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --glow:      rgba(59,130,246,0.25);
}

/* ── Full app background ── */
.stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Headings ── */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--glow) !important;
    outline: none !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.4rem !important;
    cursor: pointer !important;
    transition: opacity 0.2s, transform 0.1s, box-shadow 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    box-shadow: 0 0 18px var(--glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Cards (custom HTML) ── */
.rag-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.rag-card:hover { border-color: var(--accent); }

.answer-card {
    background: linear-gradient(135deg, #0d1f3c, #0d2233);
    border: 1px solid var(--accent);
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-top: 1rem;
    box-shadow: 0 0 30px rgba(59,130,246,0.12);
}

.source-tag {
    display: inline-block;
    background: rgba(59,130,246,0.15);
    border: 1px solid rgba(59,130,246,0.4);
    color: var(--accent2);
    border-radius: 6px;
    padding: 0.2rem 0.65rem;
    font-size: 0.78rem;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-family: 'DM Mono', monospace;
}

.stat-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1rem;
    text-align: center;
}
.stat-number {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.2rem;
}

.status-dot {
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.dot-green { background: #10b981; box-shadow: 0 0 6px #10b981; }
.dot-red   { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
.dot-grey  { background: #475569; }

.chat-bubble-user {
    background: linear-gradient(135deg, #1e3a5f, #1e3050);
    border: 1px solid #2d4f7a;
    border-radius: 14px 14px 4px 14px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    color: #bfdbfe;
    font-size: 0.93rem;
}
.chat-bubble-bot {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px 14px 14px 4px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    font-size: 0.93rem;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.8rem;
}

/* ── Alert overrides ── */
.stAlert { border-radius: 10px !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: linear-gradient(90deg, var(--accent), var(--accent2)) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []       # [{role, content, sources}]
if "sync_done" not in st.session_state:
    st.session_state.sync_done = False
if "sync_info" not in st.session_state:
    st.session_state.sync_info = {}


# ══════════════════════════════════════════════════════════════════════
# HELPERS  — talk to FastAPI backend
# ══════════════════════════════════════════════════════════════════════
def get_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def call_sync_drive():
    try:
        r = requests.post(f"{BACKEND_URL}/sync-drive", timeout=120)
        try:
            data = r.json()
        except Exception:
            data = {"error": f"Backend returned non-JSON response (HTTP {r.status_code}). Check main.py logs."}
        return data, r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach backend. Make sure main.py is running on port 8000."}, 503
    except Exception as e:
        return {"error": str(e)}, 500


def call_ask(query: str):
    try:
        r = requests.post(
            f"{BACKEND_URL}/ask",
            json={"query": query},
            timeout=60,
        )
        try:
            data = r.json()
        except Exception:
            data = {"error": f"Backend returned non-JSON response (HTTP {r.status_code}). Check main.py logs."}
        return data, r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach backend. Make sure main.py is running on port 8000."}, 503
    except Exception as e:
        return {"error": str(e)}, 500


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo / title
    st.markdown("""
    <div style='padding: 0.5rem 0 1.5rem'>
        <div style='font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;
                    background:linear-gradient(135deg,#3b82f6,#06b6d4);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
            🧠 DriveRAG
        </div>
        <div style='font-size:0.72rem;color:#64748b;margin-top:2px'>
            Ask your Google Drive documents
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Backend Status</div>', unsafe_allow_html=True)

    health = get_health()
    if health:
        st.markdown(
            f'<div class="rag-card" style="padding:0.9rem 1.1rem">'
            f'<span class="status-dot dot-green"></span>'
            f'<span style="font-size:0.85rem">Backend online</span><br>'
            f'<span style="font-size:0.75rem;color:#64748b;margin-left:15px">'
            f'{health.get("vectors_loaded",0)} vectors · {health.get("chunks_in_memory",0)} chunks</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="rag-card" style="padding:0.9rem 1.1rem;border-color:#ef4444">'
            '<span class="status-dot dot-red"></span>'
            '<span style="font-size:0.85rem;color:#ef4444">Backend offline</span><br>'
            '<span style="font-size:0.72rem;color:#64748b;margin-left:15px">'
            'Run: <code>python main.py</code></span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Sync section ──────────────────────────────────────────
    st.markdown('<div class="section-title">📂 Google Drive Sync</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.78rem;color:#64748b;margin-bottom:0.8rem">'
        'Fetches PDFs, Docs, and TXT files from your Drive, '
        'processes them, and builds the vector index.</p>',
        unsafe_allow_html=True,
    )

    if st.button("⚡ Sync Drive Now", key="sync_btn"):
        with st.spinner("Connecting to Google Drive …"):
            data, status = call_sync_drive()

        if status == 200:
            st.session_state.sync_done = True
            st.session_state.sync_info = data
            st.success(f"✅ Synced {data.get('files_processed', 0)} files · {data.get('total_chunks', 0)} chunks")
        else:
            st.error(f"❌ {data.get('error', 'Sync failed')}")

    if st.session_state.sync_done and st.session_state.sync_info:
        info = st.session_state.sync_info
        files = info.get("files", [])
        if files:
            st.markdown('<div class="section-title" style="margin-top:1rem">Indexed Files</div>', unsafe_allow_html=True)
            for fname in files:
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#94a3b8;padding:0.25rem 0;'
                    f'border-bottom:1px solid #1e2d4a">📄 {fname}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Clear chat ─────────────────────────────────────────────
    if st.button("🗑 Clear Chat", key="clear_btn"):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.7rem;color:#334155;text-align:center">'
        'RAG · FAISS · SentenceTransformers<br>Groq LLM · FastAPI backend'
        '</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════

# ── Hero header ───────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:2rem'>
    <h1 style='font-family:Syne,sans-serif;font-size:2.2rem;font-weight:800;
               background:linear-gradient(135deg,#e2e8f0,#3b82f6);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin-bottom:0.3rem'>
        Ask Your Documents
    </h1>
    <p style='color:#64748b;font-size:0.88rem'>
        Sync your Google Drive → Ask anything → Get answers grounded in your files
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats row ─────────────────────────────────────────────────────────
health = get_health()
col1, col2, col3, col4 = st.columns(4)

with col1:
    vecs = health.get("vectors_loaded", 0) if health else 0
    st.markdown(f'<div class="stat-box"><div class="stat-number">{vecs}</div><div class="stat-label">Vectors Indexed</div></div>', unsafe_allow_html=True)

with col2:
    chunks = health.get("chunks_in_memory", 0) if health else 0
    st.markdown(f'<div class="stat-box"><div class="stat-number">{chunks}</div><div class="stat-label">Chunks Loaded</div></div>', unsafe_allow_html=True)

with col3:
    files_synced = len(st.session_state.sync_info.get("files", [])) if st.session_state.sync_info else 0
    st.markdown(f'<div class="stat-box"><div class="stat-number">{files_synced}</div><div class="stat-label">Files Synced</div></div>', unsafe_allow_html=True)

with col4:
    q_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])
    st.markdown(f'<div class="stat-box"><div class="stat-number">{q_count}</div><div class="stat-label">Questions Asked</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown('<div class="section-title">💬 Conversation</div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble-user">🙋 <strong>You</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            sources_html = ""
            if msg.get("sources"):
                tags = "".join(f'<span class="source-tag">📄 {s}</span>' for s in msg["sources"])
                sources_html = f'<div style="margin-top:0.8rem"><span style="font-size:0.72rem;color:#64748b">Sources: </span>{tags}</div>'

            # Convert newlines to <br> so formatted answers render correctly
            answer_html = msg["content"].replace("\n", "<br>")

            st.markdown(
                f'<div class="chat-bubble-bot">🧠 <strong>DriveRAG</strong><br><br>'
                f'<span style="color:#cbd5e1;line-height:1.8">{answer_html}</span>'
                f'{sources_html}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

# ── Question input ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔍 Ask a Question</div>', unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    user_query = st.text_input(
        label="Ask a question",
        placeholder="e.g. What is the refund policy? / Summarize the compliance rules …",
        key="query_input",
        label_visibility="collapsed",
    )
with col_btn:
    ask_clicked = st.button("Ask →", key="ask_btn")

# ── Suggested prompts ──────────────────────────────────────────────────
st.markdown('<div style="margin-top:0.5rem;margin-bottom:1.2rem">', unsafe_allow_html=True)
sc1, sc2, sc3, sc4 = st.columns(4)
suggestion = None
with sc1:
    if st.button("📋 Summarize docs", key="s1"): suggestion = "Give me a summary of all the documents."
with sc2:
    if st.button("📜 Key policies", key="s2"):   suggestion = "What are the key policies mentioned?"
with sc3:
    if st.button("📅 Important dates", key="s3"): suggestion = "List any important dates or deadlines."
with sc4:
    if st.button("⚠️ Risks / issues", key="s4"): suggestion = "What risks or issues are mentioned?"
st.markdown('</div>', unsafe_allow_html=True)

# ── Handle question ────────────────────────────────────────────────────
final_query = suggestion or (user_query.strip() if ask_clicked and user_query.strip() else None)

if final_query:
    # guard: backend must be up
    if not get_health():
        st.error("❌ Backend is offline. Start it with: `python main.py`")
    elif not st.session_state.sync_done and (not health or health.get("vectors_loaded", 0) == 0):
        st.warning("⚠️ No documents indexed yet. Click **⚡ Sync Drive Now** in the sidebar first.")
    else:
        # append user message
        st.session_state.chat_history.append({"role": "user", "content": final_query, "sources": []})

        with st.spinner("Searching your documents …"):
            data, status = call_ask(final_query)

        if status == 200:
            answer  = data.get("answer", "No answer returned.")
            sources = data.get("sources", [])
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })
        else:
            err = data.get("error", "Unknown error")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"❌ Error: {err}",
                "sources": [],
            })

        st.rerun()

# ── Empty state ────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("""
    <div style='text-align:center;padding:3.5rem 1rem;color:#334155'>
        <div style='font-size:3.5rem;margin-bottom:1rem'>🧠</div>
        <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#475569;margin-bottom:0.5rem'>
            No conversation yet
        </div>
        <div style='font-size:0.82rem;color:#334155;max-width:360px;margin:0 auto'>
            1. Click <strong style="color:#3b82f6">⚡ Sync Drive Now</strong> in the sidebar<br>
            2. Type a question above or pick a suggestion<br>
            3. Get answers grounded in your documents
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Last answer detail card ────────────────────────────────────────────
bot_msgs = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
if bot_msgs:
    last = bot_msgs[-1]
    if last.get("sources"):
        with st.expander("📎 Sources used in last answer", expanded=False):
            for src in last["sources"]:
                st.markdown(f"- 📄 `{src}`")