"""Reddit scraping helpers for collecting candidate posts and comments."""

from __future__ import annotations

from typing import Any, Dict, List

import praw
from prawcore.exceptions import PrawcoreException

from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_SORT,
    DEFAULT_TIME_FILTER,
    MIN_COMMENT_WORDS,
    REDDIT_SEARCH_LIMIT,
    SUBREDDITS,
    TOP_COMMENT_LIMIT,
    USER_AGENT,
)


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert a value to int without allowing exceptions to escape."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float without allowing exceptions to escape."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str:
    """Normalize comment and post text into a readable string."""

    if value is None:
        return ""
    return str(value).strip()


def create_reddit_client() -> praw.Reddit:
    """Create and return a configured PRAW client."""

    try:
        return praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to initialize Reddit client: {exc}") from exc


def get_post_comments(post: Any) -> List[Dict[str, Any]]:
    """Return the top comments for a post as a clean list of dictionaries."""

    comments: List[Dict[str, Any]] = []

    try:
        post.comments.replace_more(limit=0)
        all_comments = list(post.comments.list())
        all_comments.sort(key=lambda comment: _safe_int(getattr(comment, "score", 0)), reverse=True)

        for comment in all_comments[:TOP_COMMENT_LIMIT]:
            body = _clean_text(getattr(comment, "body", ""))
            if not body or body in {"[deleted]", "[removed]"}:
                continue

            comments.append(
                {
                    "text": body,
                    "score": _safe_int(getattr(comment, "score", 0)),
                    "author": _clean_text(getattr(comment, "author", "unknown")) or "unknown",
                    "reddit_link": f"https://www.reddit.com{getattr(comment, 'permalink', '')}",
                    "word_count": len(body.split()),
                }
            )
    except PrawcoreException as exc:
        print(f"Reddit comment fetch failed for post '{getattr(post, 'title', 'unknown')}': {exc}")
    except Exception as exc:
        print(f"Unexpected error while reading comments for '{getattr(post, 'title', 'unknown')}': {exc}")

    return comments


def search_reddit(query: str, limit: int = REDDIT_SEARCH_LIMIT) -> List[Dict[str, Any]]:
    """Search configured subreddits and return structured Reddit posts and comments."""

    query = _clean_text(query)
    if not query:
        print("Reddit search skipped because the query was empty.")
        return []

    try:
        reddit = create_reddit_client()
    except RuntimeError as exc:
        print(exc)
        return []

    collected_posts: List[Dict[str, Any]] = []
    seen_urls = set()

    for subreddit_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.search(query, limit=limit, sort=DEFAULT_SORT, time_filter=DEFAULT_TIME_FILTER):
                try:
                    post_url = f"https://www.reddit.com{getattr(post, 'permalink', '')}"
                    if post_url in seen_urls:
                        continue

                    comments = get_post_comments(post)
                    record = {
                        "title": _clean_text(getattr(post, "title", "Untitled Post")) or "Untitled Post",
                        "selftext": _clean_text(getattr(post, "selftext", "")),
                        "score": _safe_int(getattr(post, "score", 0)),
                        "url": post_url,
                        "upvote_ratio": round(_safe_float(getattr(post, "upvote_ratio", 0.0)) * 100, 2),
                        "num_comments": _safe_int(getattr(post, "num_comments", len(comments))),
                        "subreddit": _clean_text(getattr(getattr(post, "subreddit", None), "display_name", subreddit_name))
                        or subreddit_name,
                        "id": _clean_text(getattr(post, "id", "")),
                        "comments": comments,
                    }
                    collected_posts.append(record)
                    seen_urls.add(post_url)
                except PrawcoreException as exc:
                    print(f"Reddit post fetch failed in r/{subreddit_name}: {exc}")
                except Exception as exc:
                    print(f"Unexpected error while processing r/{subreddit_name}: {exc}")
        except PrawcoreException as exc:
            print(f"Unable to read r/{subreddit_name}: {exc}")
        except Exception as exc:
            print(f"Unexpected subreddit error for r/{subreddit_name}: {exc}")

    collected_posts.sort(key=lambda item: item.get("score", 0), reverse=True)
    return collected_posts


def fetch_top_posts(query: str, limit: int = REDDIT_SEARCH_LIMIT) -> List[Dict[str, Any]]:
    """Backward-compatible wrapper around search_reddit."""

    return search_reddit(query, limit=limit)
