"""Offline pipeline: load docs → split into chunks → embed → store in Pinecone."""
import os
import hashlib
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from config import DATA_DIR, INDEX_NAME, EMBED_DIM, get_embeddings

# 1. LOADERS: one per file type; each returns Document(page_content, metadata)
LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": lambda p: TextLoader(p, encoding="utf-8"),
    ".md": lambda p: TextLoader(p, encoding="utf-8"),
}

def load_docs():
    docs = []
    for path in DATA_DIR.rglob("*"):
        loader = LOADERS.get(path.suffix.lower())
        if loader:
            loaded = loader(str(path)).load()
            for d in loaded:
                d.metadata["source"] = path.name   # short name for citations
            docs.extend(loaded)
    return docs

# 2. CHUNKING: ~800 chars ≈ 200 tokens, which fits MiniLM's 256-token limit.
#    Overlap keeps sentences that sit on a boundary intact.
def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    return splitter.split_documents(docs)

# 3. STABLE IDS: the same chunk always gets the same id, so re-running
#    overwrites existing vectors instead of creating duplicates.
def chunk_id(doc):
    raw = f"{doc.metadata.get('source')}|{doc.page_content}"
    return hashlib.md5(raw.encode()).hexdigest()

# 4. VECTOR DB: create the index if it doesn't exist (dimension must equal EMBED_DIM)
def ensure_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

def main():
    docs = load_docs()
    chunks = split_docs(docs)
    print(f"Loaded {len(docs)} documents → {len(chunks)} chunks")
    print("\nSample chunk:\n", chunks[0].page_content[:300], "\n", chunks[0].metadata)

    ensure_index()
    vs = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings())
    vs.add_documents(chunks, ids=[chunk_id(c) for c in chunks])   # embeds + upserts
    print(f"\nUpserted {len(chunks)} chunks to Pinecone ✔")

if __name__ == "__main__":
    main()