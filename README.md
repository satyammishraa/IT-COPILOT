# IT Support – Agentic RAG Copilot

LangGraph agent: Router → Pinecone KB → grade → (Tavily web → grade) → answer / fallback.

## Setup
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # add keys
```

## Run
```bash
python src/ingest.py          # build the knowledge base
python src/test_retrieval.py  # sanity-check retrieval
python src/app.py             # CLI chat
streamlit run src/ui.py       # web UI
python src/eval.py            # route accuracy
```