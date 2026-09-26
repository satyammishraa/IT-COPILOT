"""One function per box in the architecture diagram.
Each node takes the State and returns a dict of the fields it updates."""
import os
from typing import Literal
from pydantic import BaseModel, Field
from tavily import TavilyClient
from langchain_pinecone import PineconeVectorStore

import prompts
from config import INDEX_NAME, TOP_K, get_embeddings, get_llm

# ---------- clients (created once, when the module is imported) ----------
vs = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings())
retriever = vs.as_retriever(search_kwargs={"k": TOP_K})
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
llm = get_llm(temperature=0)

# ---------- structured outputs: the LLM must return exactly these shapes ----------
class RouteDecision(BaseModel):
    route: Literal["kb", "direct"]
    reason: str = Field(description="One short sentence explaining the choice")

class EvidenceGrade(BaseModel):
    grade: Literal["good", "weak"]
    reason: str = Field(description="One short sentence explaining the grade")

router_llm = llm.with_structured_output(RouteDecision)
grader_llm = llm.with_structured_output(EvidenceGrade)

# ---------- helpers ----------
def format_docs(docs):
    return "\n\n".join(
        f"[{i+1}] (source: {d.metadata.get('source')})\n{d.page_content}"
        for i, d in enumerate(docs)
    )

def format_web(results):
    return "\n\n".join(
        f"[{i+1}] {r.get('title')} ({r.get('url')})\n{r.get('content')}"
        for i, r in enumerate(results)
    )

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

# ---------- 4. Grade KB evidence ----------
def grade_kb(state):
    if not state.get("docs"):
        return {"kb_grade": "weak", "kb_reason": "no documents retrieved"}
    g = grader_llm.invoke(prompts.GRADE_KB.format(
        question=state["question"], context=format_docs(state["docs"])))
    log("grade_kb", f"{g.grade} — {g.reason}")
    return {"kb_grade": g.grade, "kb_reason": g.reason}

# ---------- 5. Web search (Tavily) ----------
def web_search(state):
    try:
        res = tavily.search(query=state["question"], max_results=5)
        results = res.get("results", [])
    except Exception as e:           # network/API failure → treat as no evidence
        log("web_search", f"error: {e}")
        results = []
    log("web_search", f"{len(results)} results")
    return {"web_results": results}

# ---------- 6. Grade web evidence ----------
def grade_web(state):
    if not state.get("web_results"):
        return {"web_grade": "weak", "web_reason": "no web results"}
    g = grader_llm.invoke(prompts.GRADE_WEB.format(
        question=state["question"], context=format_web(state["web_results"])))
    log("grade_web", f"{g.grade} — {g.reason}")
    return {"web_grade": g.grade, "web_reason": g.reason}

# ---------- 7. Generate from KB ----------
def gen_kb(state):
    ans = llm.invoke(prompts.GEN_KB.format(
        question=state["question"], context=format_docs(state["docs"]))).content
    cites = sorted({d.metadata.get("source") for d in state["docs"]})
    return {"answer": ans, "source": "kb", "citations": cites}

# ---------- 8. Generate from web ----------
def gen_web(state):
    ans = llm.invoke(prompts.GEN_WEB.format(
        question=state["question"], context=format_web(state["web_results"]))).content
    cites = [r.get("url") for r in state["web_results"]]
    return {"answer": ans, "source": "web", "citations": cites}

# ---------- 9. Fallback ----------
def fallback(state):
    ans = get_llm(temperature=0.3).invoke(
        prompts.FALLBACK.format(question=state["question"])).content
    return {"answer": ans, "source": "fallback", "citations": []}

# ---------- Direct (general conversation) ----------
def direct(state):
    ans = get_llm(temperature=0.5).invoke(
        prompts.DIRECT.format(question=state["question"])).content
    return {"answer": ans, "source": "direct", "citations": []}