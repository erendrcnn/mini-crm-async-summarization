"""
[NLP - Natural Language Processing]

Simple, deterministic extractive summarizer (no external services) with optional LLM-based summarization via local Ollama.

Approach (summarize):
- Split into sentences using punctuation boundaries.
- Build word frequencies (lowercased, basic stopword removal).
- Score each sentence by sum of its token frequencies.
- Pick top sentences (preserving original order) within limits.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Optional

import os
import requests

try:
    # Optional settings if available
    from app.core.config import settings  # type: ignore
except Exception:  # pragma: no cover - fallback when settings import not available
    settings = None  # type: ignore


_DEFAULT_MAX_CHARS = 300
_DEFAULT_MAX_SENTENCES = 3
_DEFAULT_MIN_SENT_CHARS = 20

_DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# Summarization via LLM (optional)
_DEFAULT_SUMMARIZE_PROVIDER = "extractive"  # "extractive" | "ollama"
_DEFAULT_SUMMARIZE_MODEL = "llama3.1"


# Minimal EN + TR stopwords (curated subset to keep it lightweight)
_STOPWORDS = {
    # English
    "the","a","an","and","or","but","if","then","else","when","while","for","to","of","in","on","at","by","with","from","as","is","are","was","were","be","been","being","it","this","that","these","those","i","you","he","she","we","they","them","his","her","their","our","your","my","me","us","do","does","did","doing","so","not","no","yes","can","could","should","would","may","might","will","just","about","into","over","after","before","than","also","too","very",
    # Turkish (subset)
    "ve","veya","ama","fakat","ancak","ile","de","da","mi","mu","mı","mü","bir","bu","şu","o","için","gibi","ile","ya","hem","hemde","daha","çok","az","en","ki","ne","nasıl","niçin","neden","çünkü","değil","var","yok","hangi","her","bazı","hiç","şey","biz","siz","ben","sen","onlar","olarak","olan","olanlar","kadar","sonra","önce","ise","yada","veya",
}


_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+|\n\s*\n+", re.UNICODE)
_TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)


def _limits() -> Tuple[int, int, int]:
    max_chars = getattr(settings, "SUMMARY_MAX_CHARS", _DEFAULT_MAX_CHARS) if settings else _DEFAULT_MAX_CHARS
    max_sentences = getattr(settings, "SUMMARY_MAX_SENTENCES", _DEFAULT_MAX_SENTENCES) if settings else _DEFAULT_MAX_SENTENCES
    min_sent_chars = getattr(settings, "SUMMARY_MIN_SENT_CHARS", _DEFAULT_MIN_SENT_CHARS) if settings else _DEFAULT_MIN_SENT_CHARS
    return int(max_chars), int(max_sentences), int(min_sent_chars)


def _sentences(text: str) -> List[str]:
    parts = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s and s.strip()]
    # Merge overly short fragments with their neighbor to avoid degenerate summaries
    merged: List[str] = []
    buf = ""
    for p in parts:
        if not buf:
            buf = p
        else:
            if len(buf) < 40 or (not buf.endswith(tuple(".!?…")) and len(buf) < 80):
                buf = f"{buf} {p}"
            else:
                merged.append(buf)
                buf = p
    if buf:
        merged.append(buf)
    return merged if merged else parts


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _summarize_extractive(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    max_chars, max_sentences, min_sent_chars = _limits()

    sents = _sentences(text)
    if not sents:
        return text[:max_chars] + ("…" if len(text) > max_chars else "")

    tokens = _tokenize(text)
    freqs = {}
    for tok in tokens:
        if tok.isdigit() or len(tok) <= 2 or tok in _STOPWORDS:
            continue
        freqs[tok] = freqs.get(tok, 0) + 1

    if not freqs:
        out: List[str] = []
        total = 0
        for s in sents:
            if total and total + 1 + len(s) > max_chars:
                break
            out.append(s)
            total += (0 if total == 0 else 1) + len(s)
            if len(out) >= max_sentences:
                break
        result = " ".join(out)
        return result if len(result) <= max_chars else (result[:max_chars] + "…")

    max_f = max(freqs.values()) or 1

    scored: List[Tuple[int, float, str]] = []
    for idx, s in enumerate(sents):
        toks = _tokenize(s)
        length_penalty = 0.8 if len(s) < min_sent_chars else 1.0
        score = 0.0
        for t in toks:
            if t in _STOPWORDS or t.isdigit() or len(t) <= 2:
                continue
            score += (freqs.get(t, 0) / max_f)
        score *= length_penalty
        scored.append((idx, score, s))

    top = sorted(scored, key=lambda x: x[1], reverse=True)[:max_sentences]
    top_sorted = [s for _, _, s in sorted(top, key=lambda x: x[0])]
    summary = " ".join(top_sorted)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "…"
    return summary


def _summarize_ollama(
    text: str,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    temperature: float = 0.2,
    timeout: float = 60.0,
) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    max_chars, max_sentences, _ = _limits()
    host = (
        host
        or (getattr(settings, "OLLAMA_HOST", None) if settings else None)
        or os.environ.get("OLLAMA_HOST")
        or _DEFAULT_OLLAMA_HOST
    )
    model = (
        model
        or (getattr(settings, "SUMMARIZE_LLM_MODEL", None) if settings else None)
        or os.environ.get("SUMMARIZE_LLM_MODEL")
        or _DEFAULT_SUMMARIZE_MODEL
    )

    # Prompt geared for concise, faithful summaries
    prompt = (
        f"Summarize the following text in at most {max_sentences} sentence(s). "
        f"Use plain text, no bullets. Keep key facts and names. "
        f"Hard limit: at most {max_chars} characters total.\n\n"
        f"=== TEXT START ===\n{text}\n=== TEXT END ==="
    )

    host = host or _DEFAULT_OLLAMA_HOST
    url = str(host).rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        out = (data.get("response") or "").strip()
        if not out:
            return _summarize_extractive(text)
        # Truncate just in case the model ignores constraints
        return out[:max_chars].rstrip()
    except Exception:
        # Fallback to extractive if LLM not available
        return _summarize_extractive(text)


def summarize(text: str) -> str:
    provider = (
        (getattr(settings, "SUMMARIZE_PROVIDER", None) if settings else None)
        or os.environ.get("SUMMARIZE_PROVIDER")
        or _DEFAULT_SUMMARIZE_PROVIDER
    ).lower()

    if provider == "ollama":
        return _summarize_ollama(text)
    # default extractive
    return _summarize_extractive(text)
