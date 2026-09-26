"""Baseline RAG: retrieve → stuff the context into the prompt → answer. No agent logic yet."""
from langchain_pinecone import PineconeVectorStore
from config import INDEX_NAME, TOP_K, get_embeddings, get_llm

vs = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings())
retriever = vs.as_retriever(search_kwargs={"k": TOP_K})
llm = get_llm()

def format_docs(docs):
    return "\n\n".join(
        f"[{i+1}] (source: {d.metadata.get('source')})\n{d.page_content}"
        for i, d in enumerate(docs)
    )

def ask(question: str) -> str:
    docs = retriever.invoke(question)
    prompt = f"""You are an IT support assistant. Answer ONLY using the context below.
If the context does not contain the answer, reply exactly: "I don't know".
Cite sources like [1].

Context:
{format_docs(docs)}

Question: {question}"""
    return llm.invoke(prompt).content

if __name__ == "__main__":
    for q in ["How do I reset my password?",
              "What is the latest Windows 11 feature update?"]:   # not in the KB
        print(f"\nQ: {q}\nA: {ask(q)}")