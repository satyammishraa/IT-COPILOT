"""Wires the nodes into the agentic flow from the diagram.
Conditional edges are where the agent makes its decisions."""
from langgraph.graph import StateGraph, START, END
from state import State
from nodes import (router, retrieve, grade_kb, gen_kb, web_search,
                   grade_web, gen_web, fallback, direct)

def build_graph():
    g = StateGraph(State)

    g.add_node("router", router)
    g.add_node("retrieve", retrieve)
    g.add_node("grade_kb", grade_kb)
    g.add_node("gen_kb", gen_kb)
    g.add_node("web_search", web_search)
    g.add_node("grade_web", grade_web)
    g.add_node("gen_web", gen_web)
    g.add_node("fallback", fallback)
    g.add_node("direct", direct)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s["route"],
                            {"kb": "retrieve", "direct": "direct"})
    g.add_edge("retrieve", "grade_kb")
    g.add_conditional_edges("grade_kb", lambda s: s["kb_grade"],
                            {"good": "gen_kb", "weak": "web_search"})
    g.add_edge("web_search", "grade_web")
    g.add_conditional_edges("grade_web", lambda s: s["web_grade"],
                            {"good": "gen_web", "weak": "fallback"})

    for n in ["gen_kb", "gen_web", "fallback", "direct"]:
        g.add_edge(n, END)

    return g.compile()

app = build_graph()

if __name__ == "__main__":
    # Paste the output into https://mermaid.live to see your graph
    print(app.get_graph().draw_mermaid())