"""Ranking logic for choosing the best Reddit answer from collected comments."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from config import MIN_COMMENT_WORDS, TOP_DISPLAY_RESULTS


SOLUTION_WORDS = {"try", "use", "install", "run", "fix", "solution", "answer", "worked"}


def extract_query_keywords(query: str) -> List[str]:
    """Extract simple keywords from the user query for scoring relevance."""

    return [word for word in re.findall(r"[a-zA-Z0-9']+", query.lower()) if len(word) > 3]


def _tokenize(text: str) -> List[str]:
    """Tokenize text into searchable lowercase terms."""

    return re.findall(r"[a-zA-Z0-9']+", text.lower())


def _normalize_upvote_score(comment_score: int) -> float:
    """Normalize raw comment score into a 0 to 30 range."""

    if comment_score <= 0:
        return 0.0
    capped_score = min(comment_score, 500)
    return round((capped_score / 500) * 30, 2)


def _length_score(word_count: int) -> float:
    """Score comment length with a bonus for practical answer lengths."""

    if word_count < 20:
        return 0.0
    if 50 <= word_count <= 500:
        return 20.0
    if word_count < 50:
        return round((word_count / 50) * 20, 2)

    if word_count <= 800:
        return round(max(0.0, 20 - ((word_count - 500) / 300) * 20), 2)
    return 0.0


def _solution_word_score(tokens: Iterable[str]) -> float:
    """Score the presence of solution-oriented words in a comment."""

    token_set = set(tokens)
    matches = len(SOLUTION_WORDS.intersection(token_set))
    if matches == 0:
        return 0.0
    return round(min(10.0, matches * (10.0 / len(SOLUTION_WORDS))), 2)


def score_comment(comment_text: str, query: str, comment_score: int = 0) -> float:
    """Score a comment from 0 to 100 using relevance, score, length, and solution cues."""

    text = (comment_text or "").strip()
    if not text:
        return 0.0

    comment_tokens = _tokenize(text)
    query_keywords = extract_query_keywords(query)

    if not comment_tokens or len(comment_tokens) < MIN_COMMENT_WORDS:
        return 0.0

    keyword_hits = sum(1 for keyword in query_keywords if keyword in text.lower())
    keyword_score = 0.0
    if query_keywords:
        keyword_score = round((keyword_hits / len(query_keywords)) * 40, 2)

    upvote_score = _normalize_upvote_score(comment_score)
    length_score = _length_score(len(comment_tokens))
    solution_score = _solution_word_score(comment_tokens)

    total_score = keyword_score + upvote_score + length_score + solution_score
    return round(max(0.0, min(total_score, 100.0)), 2)


def classify_posts(posts: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Score every comment in every post and return the top five candidates."""

    ranked_comments: List[Dict[str, Any]] = []

    try:
        for post in posts:
            comments = post.get("comments", [])
            for comment in comments:
                comment_text = (comment.get("text") or comment.get("body") or "").strip()
                if len(comment_text.split()) < MIN_COMMENT_WORDS:
                    continue

                comment_score = int(comment.get("score", 0) or 0)
                rank_score = score_comment(comment_text, query, comment_score=comment_score)
                if rank_score <= 0:
                    continue

                ranked_comments.append(
                    {
                        "comment_text": comment_text,
                        "score": rank_score,
                        "parent_post_title": post.get("title", "Untitled Post"),
                        "parent_post_url": post.get("url", ""),
                        "reddit_link": comment.get("reddit_link") or post.get("url", ""),
                    }
                )
    except Exception as exc:
        print(f"Comment classification failed: {exc}")
        return []

    ranked_comments.sort(key=lambda item: item["score"], reverse=True)
    return ranked_comments[:TOP_DISPLAY_RESULTS]


def rank_best_comments(posts: List[Dict[str, Any]], query: str, top_n: int = TOP_DISPLAY_RESULTS) -> List[Dict[str, Any]]:
    """Backward-compatible wrapper around classify_posts."""

    return classify_posts(posts, query)[:top_n]
