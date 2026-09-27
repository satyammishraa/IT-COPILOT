"""One function per box in the architecture diagram.
Each node takes the State and returns a dict of the fields it updates."""
from typing import Literal, List
from pydantic import BaseModel, Field
from ddgs import DDGS
from langchain_pinecone import PineconeVectorStore

import prompts
from config import INDEX_NAME, TOP_K, get_embeddings, get_llm

# ---------- clients (created once, when the module is imported) ----------
vs = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings())
retriever = vs.as_retriever(search_kwargs={"k": TOP_K})
llm = get_llm(temperature=0)

WEB_MAX_RESULTS = 8

# ---------- structured outputs: the LLM must return exactly these shapes ----------
class RouteDecision(BaseModel):
    route: Literal["kb", "direct"]
    reason: str = Field(description="One short sentence explaining the choice")

class EvidenceGrade(BaseModel):
    grade: Literal["good", "partial", "weak"]
    relevant: List[int] = Field(default_factory=list,
                                description="Numbers of the relevant items, e.g. [1, 3]")
    reason: str = Field(description="One short sentence explaining the grade")

router_llm = llm.with_structured_output(RouteDecision)
grader_llm = llm.with_structured_output(EvidenceGrade)

# ---------- helpers ----------
def format_docs(docs, prefix="KB"):
    if not docs:
        return "(none)"
    return "\n\n".join(
        f"[{prefix}{i+1}] (source: {d.metadata.get('source')})\n{d.page_content}"
        for i, d in enumerate(docs)
    )

def format_web(results, prefix="W"):
    if not results:
        return "(none)"
    return "\n\n".join(
        f"[{prefix}{i+1}] {r.get('title')} ({r.get('url')})\n{r.get('content')}"
        for i, r in enumerate(results)
    )

def pick(items, numbers):
    """Keep only the items whose 1-based number the grader listed."""
    return [items[n - 1] for n in numbers if isinstance(n, int) and 1 <= n <= len(items)]

def kb_citations(docs):
    return [f"KB{i+1}: {d.metadata.get('source')}" for i, d in enumerate(docs)]

def web_citations(results):
    return [f"W{i+1}: {r.get('url')}" for i, r in enumerate(results) if r.get("url")]

def log(node, msg):
    print(f"  ↳ [{node}] {msg}")

# ---------- 2. Router ----------
def router(state):
    d = router_llm.invoke(prompts.ROUTER.format(question=state["question"]))
    log("router", f"{d.route} — {d.reason}")
    return {"route": d.route}

# ---------- 3. Retrieve from Pinecone ----------
def retrieve(state):
    docs = retriever.invoke(state["question"])
    log("retrieve", f"{len(docs)} chunks: {[d.metadata.get('source') for d in docs]}")
    return {"docs": docs}

# ---------- 4. Grade KB evidence (+ keep only the relevant chunks) ----------
def grade_kb(state):
    docs = state.get("docs") or []
    if not docs:
        return {"kb_grade": "weak", "kb_reason": "no documents retrieved", "kb_docs_used": []}
    g = grader_llm.invoke(prompts.GRADE_KB.format(
        question=state["question"], context=format_docs(docs, prefix="")))
    used = pick(docs, g.relevant)
    if g.grade == "weak":
        used = []
    elif not used:               # said good/partial but listed nothing → keep all, to be safe
        used = docs
    log("grade_kb", f"{g.grade} — {g.reason} | using: {[d.metadata.get('source') for d in used]}")
    return {"kb_grade": g.grade, "kb_reason": g.reason, "kb_docs_used": used}

# ---------- 5. Web search (query rewrite + DuckDuckGo) ----------
def rewrite_query(state):
    """Turn the user's question into a good public search query (the dashed arrow in the diagram)."""
    try:
        q = llm.invoke(prompts.REWRITE_WEB_QUERY.format(
            question=state["question"],
            context=format_docs(state.get("kb_docs_used") or []))).content
        q = (q or "").strip().strip('"')
        q = q.splitlines()[0].strip() if q else ""
        return q or state["question"]
    except Exception:
        return state["question"]

def web_search(state):
    query = rewrite_query(state)
    log("web_search", f"query: {query!r}")
    try:
        raw = DDGS().text(query, max_results=WEB_MAX_RESULTS)
        # Rename DuckDuckGo's fields (title/href/body) to the shape the rest of the graph expects
        results = [
            {"title": r.get("title"), "url": r.get("href"), "content": r.get("body")}
            for r in raw
        ]
    except Exception as e:           # rate limit / network error → treat as no evidence
        log("web_search", f"error: {e}")
        results = []
    log("web_search", f"{len(results)} results")
    return {"web_query": query, "web_results": results}

# ---------- 6. Grade web evidence (+ keep only the relevant results) ----------
def grade_web(state):
    results = state.get("web_results") or []
    if not results:
        return {"web_grade": "weak", "web_reason": "no web results", "web_used": []}
    g = grader_llm.invoke(prompts.GRADE_WEB.format(
        question=state["question"], context=format_web(results, prefix="")))
    used = pick(results, g.relevant)
    if g.grade == "weak":
        used = []
    elif not used:
        used = results
    log("grade_web", f"{g.grade} — {g.reason} | using {len(used)} of {len(results)}")
    return {"web_grade": g.grade, "web_reason": g.reason, "web_used": used}

# ---------- 7. Generate from KB ----------
def gen_kb(state):
    docs = state.get("kb_docs_used") or state.get("docs") or []
    ans = llm.invoke(prompts.GEN_KB.format(
        question=state["question"], context=format_docs(docs))).content
    return {"answer": ans, "source": "kb", "citations": kb_citations(docs)}

# ---------- 8. Generate from web (+ any partial KB facts) ----------
def gen_web(state):
    kb = state.get("kb_docs_used") or []
    web = state.get("web_used") or []
    ans = llm.invoke(prompts.GEN_WEB.format(
        question=state["question"],
        kb_context=format_docs(kb),
        web_context=format_web(web))).content
    return {"answer": ans,
            "source": "kb+web" if kb else "web",
            "citations": kb_citations(kb) + web_citations(web)}

# ---------- 9. Fallback (uses whatever evidence exists) ----------
def fallback(state):
    kb = state.get("kb_docs_used") or []
    web = state.get("web_used") or []
    ans = get_llm(temperature=0.3).invoke(prompts.FALLBACK.format(
        question=state["question"],
        kb_context=format_docs(kb),
        web_context=format_web(web))).content
    return {"answer": ans, "source": "fallback",
            "citations": kb_citations(kb) + web_citations(web)}

# ---------- Direct (general conversation) ----------
def direct(state):
    ans = get_llm(temperature=0.5).invoke(
        prompts.DIRECT.format(question=state["question"])).content
    return {"answer": ans, "source": "direct", "citations": []}