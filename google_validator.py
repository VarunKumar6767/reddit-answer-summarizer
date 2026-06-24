"""Google snippet validation helpers for cross-checking a Reddit answer."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from config import GOOGLE_HEADERS, GOOGLE_RATE_LIMIT_SECONDS, GOOGLE_RESULT_LIMIT, GOOGLE_TIMEOUT_SECONDS


_LAST_GOOGLE_REQUEST_AT = 0.0


def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text for snippet comparison."""

    return [word for word in re.findall(r"[a-zA-Z0-9']+", (text or "").lower()) if len(word) > 3]


def _respect_rate_limit() -> None:
    """Pause between Google requests to reduce blocking risk."""

    global _LAST_GOOGLE_REQUEST_AT

    now = time.monotonic()
    elapsed = now - _LAST_GOOGLE_REQUEST_AT
    if _LAST_GOOGLE_REQUEST_AT > 0 and elapsed < GOOGLE_RATE_LIMIT_SECONDS:
        time.sleep(GOOGLE_RATE_LIMIT_SECONDS - elapsed)


def _is_blocked_response(response: requests.Response) -> bool:
    """Detect whether Google has blocked or challenged the request."""

    body = response.text.lower()
    return bool(
        response.status_code in {403, 429, 503}
        or "unusual traffic" in body
        or "our systems have detected" in body
        or "captcha" in body
        or "/sorry/" in response.url.lower()
    )


def google_search(query: str) -> List[str]:
    """Search Google and collect the top result snippets as plain text."""

    global _LAST_GOOGLE_REQUEST_AT

    query = (query or "").strip()
    if not query:
        return []

    _respect_rate_limit()

    try:
        response = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": GOOGLE_RESULT_LIMIT, "hl": "en"},
            headers=GOOGLE_HEADERS,
            timeout=GOOGLE_TIMEOUT_SECONDS,
        )
        _LAST_GOOGLE_REQUEST_AT = time.monotonic()
        response.raise_for_status()

        if _is_blocked_response(response):
            raise RuntimeError("Google blocked the request")

        soup = BeautifulSoup(response.text, "lxml")
        snippets: List[str] = []

        for result in soup.select("div.g"):
            snippet_parts = result.select("h3, div.VwiC3b, span.aCOpRe, div.yXK7lf")
            combined_text = " ".join(
                part.get_text(" ", strip=True)
                for part in snippet_parts
                if part.get_text(strip=True)
            ).strip()
            if combined_text and combined_text not in snippets:
                snippets.append(combined_text)
            if len(snippets) == GOOGLE_RESULT_LIMIT:
                break

        return snippets
    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc) == "Google blocked the request":
            raise
        raise RuntimeError(f"Google search failed: {exc}") from exc


def validate_answer(reddit_answer: str, query: str) -> Dict[str, Any]:
    """Compare Reddit answer keywords with Google snippets and return a confidence score."""

    try:
        snippets = google_search(query)
        if not snippets:
            return {
                "confidence": 0,
                "matching_keywords": [],
                "snippets": [],
                "warning": "No Google snippets were returned.",
            }

        answer_keywords = set(extract_keywords(reddit_answer))
        snippet_keywords = set()
        for snippet in snippets:
            snippet_keywords.update(extract_keywords(snippet))

        if not answer_keywords or not snippet_keywords:
            return {
                "confidence": 0,
                "matching_keywords": [],
                "snippets": snippets,
                "warning": "Insufficient text to validate against Google snippets.",
            }

        matching_keywords = sorted(answer_keywords.intersection(snippet_keywords))
        confidence = int(round((len(matching_keywords) / len(answer_keywords)) * 100))
        confidence = max(0, min(confidence, 100))

        return {
            "confidence": confidence,
            "matching_keywords": matching_keywords,
            "snippets": snippets,
        }
    except RuntimeError as exc:
        return {
            "confidence": 50,
            "matching_keywords": [],
            "snippets": [],
            "warning": f"Google validation warning: {exc}",
        }
    except Exception as exc:
        return {
            "confidence": 0,
            "matching_keywords": [],
            "snippets": [],
            "warning": f"Google validation failed: {exc}",
        }


def fetch_google_snippets(query: str) -> List[str]:
    """Backward-compatible wrapper around google_search."""

    return google_search(query)


def validate_with_google(query: str, reddit_answer: str) -> Dict[str, Any]:
    """Backward-compatible wrapper around validate_answer."""

    return validate_answer(reddit_answer, query)
