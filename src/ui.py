"""IT Support Copilot: custom-styled Streamlit chat UI.
Run locally from the project root:  streamlit run src/ui.py"""
import os
import html
from urllib.parse import urlparse

import streamlit as st
from config import DATA_DIR, INDEX_NAME

st.set_page_config(page_title="IT Support Copilot", page_icon="🛠️", layout="wide")


# ---------- load the LangGraph agent once per server process ----------
@st.cache_resource(show_spinner="Loading models and connecting to the knowledge base…")
def load_agent():
    from graph import app
    return app


# ---------- constants ----------
SOURCE_BADGE = {  # source → (label, css class)
    "kb": ("📚 Internal KB", "b-kb"),
    "web": ("🌐 Web search", "b-web"),
    "kb+web": ("📚🌐 KB + Web", "b-mix"),
    "fallback": ("⚠️ Best effort", "b-fallback"),
    "direct": ("💬 General", "b-direct"),
}

SAMPLES = [
    "My VPN keeps disconnecting",
    "Can I get a MacBook instead of a Dell?",
    "I'm locked out of my account",
    "What VPN client does Acme use and is it free to download?",
    "How do I clear the DNS cache on macOS?",
    "What's new in the latest Windows 11 update?",
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stChatMessage { font-family: 'Inter', sans-serif; }
.block-container { max-width: 1050px; padding-top: 4rem; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stAppDeployButton"] { display: none; }

/* hero */
.hero { background: linear-gradient(135deg, #4f46e5 0%, #2563eb 55%, #0ea5e9 100%);
        border-radius: 20px; padding: 28px 32px; color: #fff; margin-bottom: 18px;
        box-shadow: 0 12px 30px rgba(79,70,229,.25); }
.hero h1 { font-size: 1.9rem; font-weight: 700; margin: 0 0 6px 0; color: #fff; }
.hero p  { margin: 0; opacity: .92; font-size: 1rem; }
.pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.pill  { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28);
         padding: 5px 12px; border-radius: 999px; font-size: .82rem; }

/* topic cards */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 6px 0 18px; }
.card  { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; }
.card b { display: block; margin-bottom: 4px; }
.card span { color: #6b7280; font-size: .88rem; }

/* "thinking" indicator */
.thinking { display: inline-flex; align-items: center; gap: 10px; color: #6b7280; font-size: .9rem;
            background: #fff; border: 1px solid #e5e7eb; border-radius: 999px; padding: 8px 16px; }
.dots span { display: inline-block; width: 6px; height: 6px; margin: 0 1px; border-radius: 50%;
             background: #4f46e5; animation: blink 1.2s infinite both; }
.dots span:nth-child(2) { animation-delay: .2s; }
.dots span:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 80%, 100% { opacity: .2; } 40% { opacity: 1; } }

/* answer badge + sources */
.badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: .8rem;
         font-weight: 600; margin-bottom: 8px; }
.b-kb       { background: #dcfce7; color: #166534; }
.b-web      { background: #dbeafe; color: #1e40af; }
.b-mix      { background: #ede9fe; color: #5b21b6; }
.b-fallback { background: #fef3c7; color: #92400e; }
.b-direct   { background: #f3f4f6; color: #374151; }
.srcs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.chip { font-size: .78rem; padding: 4px 10px; border-radius: 8px; border: 1px solid #e5e7eb;
        background: #f9fafb; color: #374151 !important; text-decoration: none !important; }
a.chip:hover { border-color: #2563eb; color: #2563eb !important; }

/* sidebar */
section[data-testid="stSidebar"] .stButton button { width: 100%; text-align: left; justify-content: flex-start;
        border-radius: 10px; font-size: .85rem; }
.kbfile { font-size: .85rem; padding: 3px 0; color: #374151; }
</style>
"""


# ---------- helpers ----------
def thinking_html(text):
    return (f'<div class="thinking"><span class="dots"><span></span><span></span><span></span></span>'
            f'{html.escape(text)}</div>')


def status_after(node, upd):
    """Friendly progress text to show after a graph node finishes (None = keep the current text)."""
    upd = upd or {}
    if node == "router":
        return "Checking the knowledge base…" if upd.get("route") == "kb" else "Writing a reply…"
    if node == "grade_kb":
        return "Writing the answer…" if upd.get("kb_grade") == "good" else "Searching the web…"
    if node == "grade_web":
        return "Writing the answer…"
    return None


def badge_html(source):
    label, cls = SOURCE_BADGE.get(source, (source, "b-direct"))
    return f'<span class="badge {cls}">{label}</span>'


def sources_html(citations):
    chips = []
    for c in citations or []:
        tag, _, target = c.partition(": ")
        if target.startswith("http"):
            domain = urlparse(target).netloc.replace("www.", "")
            chips.append(f'<a class="chip" href="{html.escape(target)}" target="_blank">'
                         f'{html.escape(tag)} · 🔗 {html.escape(domain)}</a>')
        else:
            chips.append(f'<span class="chip">{html.escape(tag)} · 📄 {html.escape(target)}</span>')
    return f'<div class="srcs">{"".join(chips)}</div>' if chips else ""


def render_assistant(msg):
    st.markdown(badge_html(msg["source"]), unsafe_allow_html=True)
    st.markdown(msg["answer"])
    if msg.get("citations"):
        st.markdown(sources_html(msg["citations"]), unsafe_allow_html=True)


# ---------- page ----------
st.markdown(CSS, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 🛠️ IT Support Copilot")
    st.caption("Your IT helpdesk assistant")

    st.markdown("#### Try asking")
    for q in SAMPLES:
        if st.button(q, key=f"sample-{q}"):
            st.session_state.pending = q

    st.markdown("#### Knowledge base")
    files = sorted(p.name for p in DATA_DIR.glob("*") if p.is_file())
    st.markdown("".join(f'<div class="kbfile">📄 {html.escape(f)}</div>' for f in files) or "No files",
                unsafe_allow_html=True)

    st.markdown("#### Settings")
    st.caption(f"Model: `{os.getenv('LLM_MODEL', 'not set')}`  \nIndex: `{INDEX_NAME}`")
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

# new question: typed, or clicked in the sidebar (read early so the intro hides immediately)
typed = st.chat_input("Ask an IT question…")
question = typed or st.session_state.pop("pending", None)

if not st.session_state.messages and not question:
    st.markdown(
        '<div class="hero"><h1>🛠️ IT Support Copilot</h1>'
        '<p>Ask any IT question. I check the internal knowledge base first, search the web if needed, '
        'and tell you exactly where each answer came from.</p>'
        '<div class="pills"><span class="pill">📚 Company knowledge base</span>'
        '<span class="pill">🌐 Web search when needed</span><span class="pill">🔗 Cited sources</span></div></div>'
        '<div class="cards">'
        '<div class="card"><b>🔐 Accounts &amp; passwords</b><span>Resets, lockouts and password rules.</span></div>'
        '<div class="card"><b>🌐 VPN &amp; network</b><span>Setup, disconnects and remote access.</span></div>'
        '<div class="card"><b>💻 Laptops &amp; hardware</b><span>Requests, refreshes and lost devices.</span></div>'
        '<div class="card"><b>📧 Email &amp; printing</b><span>Outlook sync issues and secure printing.</span></div>'
        '</div>', unsafe_allow_html=True)

# chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🛠️"):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            render_assistant(msg)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🛠️"):
        status_box = st.empty()
        status_box.markdown(thinking_html("Thinking…"), unsafe_allow_html=True)

        final = {"question": question}
        try:
            agent = load_agent()
            # stream_mode="updates" yields {node_name: fields_it_returned} after every node
            for chunk in agent.stream({"question": question}, stream_mode="updates"):
                for node, upd in chunk.items():
                    final.update(upd or {})
                    text = status_after(node, upd)
                    if text:
                        status_box.markdown(thinking_html(text), unsafe_allow_html=True)
        except Exception as e:
            status_box.empty()
            st.error(f"Something went wrong: {e}")
            st.stop()

        status_box.empty()
        msg = {"role": "assistant", "answer": final.get("answer", "(no answer)"),
               "source": final.get("source", "direct"), "citations": final.get("citations", [])}
        render_assistant(msg)
        st.session_state.messages.append(msg)