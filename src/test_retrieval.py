"""Check retrieval on its own, with no LLM. Higher score = closer meaning (cosine)."""
from langchain_pinecone import PineconeVectorStore
from config import INDEX_NAME, get_embeddings

vs = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings())

QUESTIONS = [
    "my vpn keeps disconnecting",
    "I got locked out of my account",
    "best pizza in Bengaluru",          # unrelated → scores should drop
]

for q in QUESTIONS:
    print(f"\n🔎 {q}")
    for doc, score in vs.similarity_search_with_score(q, k=3):
        print(f"  {score:.3f}  {doc.metadata.get('source'):<28} {doc.page_content[:70]!r}")