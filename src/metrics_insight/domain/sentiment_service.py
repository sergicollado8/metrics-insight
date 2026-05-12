from typing import List, Dict, Any
from src.metrics_insight.domain.pull_request import PullRequest
from src.metrics_insight.domain.repository_interfaces import SentimentAnalyzer


class SentimentService:
    """Domain service for analyzing sentiment in PR reviews."""

    def __init__(self, analyzer: SentimentAnalyzer):
        self.analyzer = analyzer

    def analyze_team_sentiment(self, prs: List[PullRequest]) -> Dict[str, Any]:
        """Analyzes sentiment across all PR reviews."""
        all_comments = []
        for pr in prs:
            for review in pr.reviews:
                if review.body:
                    all_comments.append(review.body)

        if not all_comments:
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "friction_detected": False,
                "summary": "No human review comments found to analyze."
            }

        return self.analyzer.analyze_sentiment(all_comments)
