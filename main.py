"""Command-line entry point for the Reddit Answer Summarizer project."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from classifier import classify_posts
from display import display_results
from google_validator import validate_answer
from scraper import search_reddit


BANNER = r"""
 ____            _     _      _ _     _                 _
|  _ \ ___  __ _| |__ | | ___| (_)___| |__   __ _ _ __ | |_
| |_) / _ \/ _` | '_ \| |/ _ \ | / __| '_ \ / _` | '_ \| __|
|  _ <  __/ (_| | |_) | |  __/ | \__ \ | | | (_| | | | | |_
|_| \_\___|\__,_|_.__/|_|\___|_|_|___/_| |_|\__,_|_| |_|\__|
""".strip("\n")


def print_banner() -> None:
    """Print the application banner."""

    print(BANNER)
    print("=" * 72)
    print("Reddit Answer Summarizer")
    print("=" * 72)


def build_summary(query: str) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """Run the full pipeline for a single query and return answers plus validation."""

    posts = search_reddit(query)
    if not posts:
        return [], {"confidence": 0, "matching_keywords": [], "snippets": [], "warning": "No Reddit posts were found."}

    top_answers = classify_posts(posts, query)
    if not top_answers:
        return [], {
            "confidence": 0,
            "matching_keywords": [],
            "snippets": [],
            "warning": "No qualifying Reddit comments were found.",
        }

    validation = validate_answer(top_answers[0]["comment_text"], query)
    return top_answers, validation


def _prompt_yes_no(message: str) -> bool:
    """Prompt until the user provides a yes or no answer."""

    while True:
        response = input(message).strip().lower()
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please enter y or n.")


def run_pipeline() -> None:
    """Collect questions, run the full workflow, and show the result."""

    print_banner()

    while True:
        try:
            query = input("Enter your question: ").strip()
            if not query:
                print("Please enter a valid question.")
                continue

            print("\nSearching Reddit...")
            print("Analyzing comments...")
            print("Validating with Google...")
            print("Building your answer...\n")

            top_answers, validation = build_summary(query)
            display_results(query, top_answers, validation)

            if not _prompt_yes_no("Search again? (y/n): "):
                print("Goodbye.")
                break
            print()
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except EOFError:
            print("\nGoodbye.")
            break
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")
            if not _prompt_yes_no("Search again? (y/n): "):
                print("Goodbye.")
                break
            print()


if __name__ == "__main__":
    run_pipeline()
