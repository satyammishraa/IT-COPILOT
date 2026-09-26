"""Runs a labelled test set and checks each question took the expected path.
Use it every time you change a prompt, chunk size or top-K."""
from graph import app

TESTS = [
    ("hi there!", "direct"),
    ("thanks, that helped", "direct"),
    ("How do I connect to the VPN?", "kb"),
    ("My VPN disconnects every few minutes", "kb"),
    ("I'm locked out after too many password attempts", "kb"),
    ("How long are print jobs held before deletion?", "kb"),
    ("Can I get a MacBook instead of a Dell?", "kb"),
    ("Outlook says Working Offline", "kb"),
    ("What's new in the latest Windows 11 feature update?", "web"),
    ("How do I clear the DNS cache on macOS?", "web"),
    ("What is the Wi-Fi password on floor 7 of the Acme Pune office?", "fallback"),
]

def main():
    passed = 0
    for q, expected in TESTS:
        out = app.invoke({"question": q})
        ok = out["source"] == expected
        passed += ok
        print(f"{'✅' if ok else '❌'} expected={expected:<8} got={out['source']:<8} {q}")
    print(f"\nRoute accuracy: {passed}/{len(TESTS)} ({passed/len(TESTS):.0%})")

if __name__ == "__main__":
    main()