"""Terminal chat. The node logs show you the path each question takes."""
from graph import app

LABEL = {
    "kb": "📚 Internal KB",
    "web": "🌐 Web search",
    "kb+web": "📚🌐 KB + Web",
    "fallback": "⚠️ Best effort (not fully verified)",
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
        print(f"\nCopilot [{LABEL.get(out['source'], out['source'])}]:\n{out['answer']}")
        if out.get("citations"):
            print("\nSources:")
            for c in out["citations"]:
                print("  -", c)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")