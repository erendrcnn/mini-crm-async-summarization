def summarize(text: str) -> str:
    # Deterministic local stub summarizer: first sentence or trimmed
    text = (text or "").strip()
    if not text:
        return ""
    # Take up to 160 chars and add ellipsis if longer
    max_len = 160
    return (text[:max_len] + ("..." if len(text) > max_len else ""))
