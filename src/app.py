"""Terminal chat. The node logs show you the path each question takes."""
from graph import app

LABEL = {
    "kb": "📚 Internal KB",
    "web": "🌐 Web search",
    "fallback": "⚠️ Best effort (no verified source)",
    "direct": "💬 General",
}

def main():
    print("IT Support Copilot — type 'exit' to quit")
    while True:
        q = input("\nYou: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        out = app.invoke({"question": q})
        print(f"\nCopilot [{LABEL[out['source']]}]:\n{out['answer']}")
        if out.get("citations"):
            print("\nSources:", ", ".join(out["citations"]))

if __name__ == "__main__":
    main()