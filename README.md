
### Live Demo
 🌐 [Click here to view Assistant](https://it-support-copilot.onrender.com/)
---
title: IT Support Copilot
emoji: 🛠️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
short_description: Agentic RAG IT helpdesk - LangGraph, Pinecone, Groq
---

# Enterprise IT Support – Agentic RAG Copilot

LangGraph agent: Router → Pinecone KB → grade (good / partial / weak) → DuckDuckGo web → grade → answer or fallback.
Every answer shows where it came from, and the UI animates the agent's path live.

## Stack
LangGraph · Pinecone · all-MiniLM-L6-v2 embeddings · Groq (gpt-oss-120b) · DuckDuckGo search · Streamlit

## Run locally
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env                            # add your keys
python src/ingest.py                            # build the knowledge base (once)
streamlit run src/ui.py                         # web UI
```

## Other scripts
```bash
python src/test_retrieval.py   # check retrieval scores
python src/app.py              # terminal chat
python src/eval.py             # route accuracy on the test set
```
