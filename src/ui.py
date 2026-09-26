"""Web chat UI. Run: streamlit run src/ui.py"""
import streamlit as st
from graph import app

LABEL = {"kb": "📚 Internal KB", "web": "🌐 Web search",
         "fallback": "⚠️ Best effort", "direct": "💬 General"}

st.set_page_config(page_title="IT Support Copilot", page_icon="🛠️")
st.title("🛠️ IT Support Copilot")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if q := st.chat_input("Ask an IT question..."):
    st.session_state.history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            out = app.invoke({"question": q})
        text = f"**{LABEL[out['source']]}**\n\n{out['answer']}"
        if out.get("citations"):
            text += "\n\n*Sources:* " + ", ".join(out["citations"])
        st.markdown(text)
        with st.expander("Agent trace"):
            st.json({k: out.get(k) for k in
                     ["route", "kb_grade", "kb_reason", "web_grade", "web_reason", "source"]})

    st.session_state.history.append({"role": "assistant", "content": text})