"""The shared state that flows through the graph.
Each node reads what it needs and returns ONLY the fields it changes."""
from typing import TypedDict, List, Any

class State(TypedDict, total=False):
    question: str
    route: str               # router decision: "kb" | "direct"
    docs: List[Any]          # KB chunks from Pinecone
    kb_grade: str            # "good" | "weak"
    kb_reason: str
    web_results: List[dict]  # Tavily results: {title, url, content, ...}
    web_grade: str           # "good" | "weak"
    web_reason: str
    answer: str
    source: str              # "kb" | "web" | "fallback" | "direct"
    citations: List[str]