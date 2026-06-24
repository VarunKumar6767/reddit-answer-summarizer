"""Central configuration for the Reddit Answer Summarizer project."""

from __future__ import annotations

import os


CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditAnswerSummarizer/1.0").strip()

GOOGLE_HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
	),
	"Accept-Language": "en-US,en;q=0.9",
}

SUBREDDITS = [
	"learnpython",
	"python",
	"programming",
	"webdev",
	"techsupport",
	"AskReddit",
	"explainlikeimfive",
	"datascience",
	"MachineLearning",
	"answers",
]

REDDIT_SEARCH_LIMIT = 20
TOP_COMMENT_LIMIT = 15
MIN_COMMENT_WORDS = 20
TOP_DISPLAY_RESULTS = 3
DISPLAY_TRUNCATION_LENGTH = 300
GOOGLE_RESULT_LIMIT = 5
GOOGLE_TIMEOUT_SECONDS = 10
GOOGLE_RATE_LIMIT_SECONDS = 3
DEFAULT_TIME_FILTER = "all"
DEFAULT_SORT = "relevance"

VERDICT_THRESHOLDS = {
	"verified": 70,
	"partial": 40,
}
