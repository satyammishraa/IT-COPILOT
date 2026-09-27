"""The shared state that flows through the graph.
Each node reads what it needs and returns ONLY the fields it changes."""
from typing import TypedDict, List, Any

class State(TypedDict, total=False):
    question: str
    route: str                 # router decision: "kb" | "direct"
    docs: List[Any]            # all chunks retrieved from Pinecone
    kb_grade: str              # "good" | "partial" | "weak"
    kb_reason: str
    kb_docs_used: List[Any]    # only the chunks the grader marked relevant
    web_query: str             # rewritten query actually sent to the search engine
    web_results: List[dict]    # all web results
    web_grade: str             # "good" | "partial" | "weak"
    web_reason: str
    web_used: List[dict]       # only the results the grader marked relevant
    answer: str
    source: str                # "kb" | "web" | "kb+web" | "fallback" | "direct"
    citations: List[str]