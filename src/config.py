"""Central config: paths, keys, and factory functions for the LLM and embeddings.
Everything else imports from here, so switching models is a one-line change."""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.embeddings import Embeddings

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_CACHE = ROOT / ".cache" / "fastembed"   # inside the project, so a cloud build can pre-download it
load_dotenv(ROOT / ".env")   # locally reads .env; in the cloud, keys come from the host's environment variables

# Remove stray spaces/newlines that often sneak in when pasting keys into a dashboard
for _key in ("GROQ_API_KEY", "PINECONE_API_KEY", "LLM_MODEL"):
    if os.getenv(_key):
        os.environ[_key] = os.environ[_key].strip()

INDEX_NAME = "it-support-kb"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384          # MiniLM outputs 384-dim vectors; the Pinecone index must match
TOP_K = 4                # chunks retrieved per question


class MiniLMEmbeddings(Embeddings):
    """all-MiniLM-L6-v2 through fastembed (ONNX runtime): same model, no PyTorch, much smaller install."""

    def __init__(self, model_name: str = EMBED_MODEL):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name, cache_dir=str(MODEL_CACHE))

    def embed_documents(self, texts):
        return [vec.tolist() for vec in self.model.embed(list(texts))]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


_embeddings = None

def get_embeddings():
    """Load the embedding model once and reuse it."""
    global _embeddings
    if _embeddings is None:
        _embeddings = MiniLMEmbeddings()
    return _embeddings

def get_llm(temperature: float = 0):
    """temperature=0 -> deterministic; use it for the router and graders."""
    return init_chat_model(os.environ["LLM_MODEL"], temperature=temperature)