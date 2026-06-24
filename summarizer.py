"""Backward-compatible CLI wrapper for the Reddit Answer Summarizer."""

from __future__ import annotations

from main import run_pipeline


def run() -> None:
    """Run the primary Reddit Answer Summarizer CLI."""

    run_pipeline()


if __name__ == "__main__":
    run()

