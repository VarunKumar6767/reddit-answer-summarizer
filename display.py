"""Terminal output helpers for the final Reddit answer summary."""

from __future__ import annotations

from textwrap import fill
from typing import Any, Dict, Iterable, List

from colorama import Fore, Style, init as colorama_init

from config import DISPLAY_TRUNCATION_LENGTH, TOP_DISPLAY_RESULTS, VERDICT_THRESHOLDS


colorama_init(autoreset=True)


def get_verdict(confidence: int) -> str:
    """Convert the Google confidence score into a user-facing verdict."""

    if confidence >= VERDICT_THRESHOLDS["verified"]:
        return "VERIFIED"
    if confidence >= VERDICT_THRESHOLDS["partial"]:
        return "PARTIALLY VERIFIED"
    return "UNVERIFIED"


def _color_for_verdict(verdict: str) -> str:
    """Choose a terminal color based on the verdict."""

    if verdict == "VERIFIED":
        return Fore.GREEN
    if verdict == "PARTIALLY VERIFIED":
        return Fore.YELLOW
    return Fore.RED


def _truncate(text: str, limit: int = DISPLAY_TRUNCATION_LENGTH) -> str:
    """Trim text to a readable terminal length."""

    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _box_width(lines: Iterable[str], minimum: int = 72) -> int:
    """Calculate a reasonable terminal box width for the provided lines."""

    widest = max((len(line) for line in lines), default=minimum)
    return max(minimum, min(widest + 4, 110))


def _print_box(lines: List[str], color: str = "") -> None:
    """Print text inside a clean ASCII box."""

    width = _box_width(lines)
    border = "+" + "-" * (width - 2) + "+"
    print(color + border + Style.RESET_ALL)
    for line in lines:
        padded = line[: width - 4]
        print(color + f"| {padded.ljust(width - 4)} |" + Style.RESET_ALL)
    print(color + border + Style.RESET_ALL)


def _normalize_validation(confidence: Any) -> Dict[str, Any]:
    """Normalize the validation payload into a dictionary."""

    if isinstance(confidence, dict):
        return confidence
    return {"confidence": int(confidence or 0), "matching_keywords": [], "snippets": []}


def display_results(query: str, top_answers: List[Dict[str, Any]], confidence: Any) -> None:
    """Print the query, best answers, validation details, and final verdict."""

    validation = _normalize_validation(confidence)
    confidence_score = int(validation.get("confidence", 0) or 0)
    verdict = get_verdict(confidence_score)
    verdict_color = _color_for_verdict(verdict)

    header_lines = [
        "Reddit Answer Summarizer",
        f"Query: {query}",
        f"Top Reddit answers shown: {min(len(top_answers), TOP_DISPLAY_RESULTS)}",
    ]
    _print_box(header_lines)
    print()

    if not top_answers:
        _print_box(["No qualifying Reddit answers were found for this query."])
    else:
        for index, answer in enumerate(top_answers[:TOP_DISPLAY_RESULTS], start=1):
            lines = [
                f"Answer #{index}",
                f"Classifier score: {answer.get('score', 0):.2f}/100",
                f"Post title: {answer.get('parent_post_title', 'Unknown Title')}",
                f"Reddit URL: {answer.get('reddit_link') or answer.get('parent_post_url', '')}",
                "Answer:",
            ]
            wrapped_answer = fill(_truncate(answer.get("comment_text", "")), width=100)
            lines.extend(wrapped_answer.splitlines() or [""])
            _print_box(lines)
            print()

    validation_lines = [
        "Google Validation",
        f"Confidence: {confidence_score}/100",
    ]
    matching_keywords = validation.get("matching_keywords") or validation.get("matched_keywords") or []
    validation_lines.append(
        f"Matching keywords: {', '.join(matching_keywords) if matching_keywords else 'None'}"
    )
    warning = validation.get("warning")
    if warning:
        validation_lines.append(f"Warning: {warning}")
    snippets = validation.get("snippets", [])
    if snippets:
        validation_lines.append("Top Google snippets:")
        for snippet in snippets[:3]:
            validation_lines.extend(fill(_truncate(snippet, 150), width=100).splitlines())
    _print_box(validation_lines)
    print()

    verdict_lines = [
        f"FINAL VERDICT: {verdict}",
        f"Google confidence: {confidence_score}/100",
    ]
    _print_box(verdict_lines, color=verdict_color)
    print()


def display_result(query: str, best_answer: Dict[str, Any], validation: Dict[str, Any]) -> None:
    """Backward-compatible wrapper for a single top answer."""

    display_results(query, [best_answer] if best_answer else [], validation)
