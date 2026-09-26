"""Central config: paths, keys, and factory functions for the LLM and embeddings.
Everything else imports from here, so switching models is a one-line change."""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
load_dotenv(ROOT / ".env")

INDEX_NAME = "it-support-kb"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384          # MiniLM outputs 384-dim vectors; the Pinecone index must match
TOP_K = 4                # chunks retrieved per question

_embeddings = None

def get_embeddings():
    """Load the embedding model once and reuse it (loading takes a few seconds)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings

def get_llm(temperature: float = 0):
    """temperature=0 → deterministic; use it for the router and graders."""
    return init_chat_model(os.environ["LLM_MODEL"], temperature=temperature)