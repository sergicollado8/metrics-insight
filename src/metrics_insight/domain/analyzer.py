from dataclasses import dataclass
from typing import List, Optional, Protocol
from src.metrics_insight.domain.pull_request import PullRequest


@dataclass(frozen=True)
class Insight:
    """Represents an actionable finding from the metrics."""
    category: str  # Bottleneck, Quality Risk, Strength, Efficiency
    title: str
    description: str
    impact: str


class AnalyzerRule(Protocol):
    """Protocol for an atomic analysis rule."""
    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        ...


class SlowReviewsRule:
    def __init__(self, threshold_h: float = 24.0):
        self.threshold_h = threshold_h

    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        slow_prs = [
            pr for pr in prs 
            if pr.first_human_review and pr.waiting_for_reviewer_h > self.threshold_h
        ]
        if not slow_prs:
            return None

        return Insight(
            category="Bottleneck",
            title="Slow Initial Review",
            description=f"{len(slow_prs)} PRs took more than {self.threshold_h} business hours to get the first review.",
            impact="Increases lead time and slows down delivery."
        )


class LargePRsRule:
    def __init__(self, threshold_size: int = 500):
        self.threshold_size = threshold_size

    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        large_prs = [pr for pr in prs if pr.size > self.threshold_size]
        if not large_prs:
            return None

        return Insight(
            category="Quality Risk",
            title="Large Pull Requests",
            description=f"{len(large_prs)} PRs are larger than {self.threshold_size} lines.",
            impact="Reduces review quality and increases the probability of bugs."
        )


class HighReworkRule:
    def __init__(self, threshold_commits: int = 5):
        self.threshold_commits = threshold_commits

    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        high_rework = [pr for pr in prs if pr.commits_after_first_review > self.threshold_commits]
        if not high_rework:
            return None

        return Insight(
            category="Quality Risk",
            title="High Rework after Review",
            description=f"{len(high_rework)} PRs had more than {self.threshold_commits} commits after the first review.",
            impact="Suggests misalignment before opening the PR or high code complexity."
        )


class JiraTraceabilityRule:
    def __init__(self, threshold_pct: float = 90.0):
        self.threshold_pct = threshold_pct

    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        if not prs:
            return None
        prs_with_jira = [pr for pr in prs if pr.has_jira_ticket]
        coverage = (len(prs_with_jira) / len(prs)) * 100
        
        if coverage < self.threshold_pct:
            return None

        return Insight(
            category="Strength",
            title="Excellent Jira Traceability",
            description=f"{coverage:.1f}% of PRs are linked to a Jira ticket.",
            impact="Ensures transparency and alignment with business goals."
        )


class ReworkTrapRule:
    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        trap_prs = [
            pr for pr in prs 
            if pr.is_merged and pr.waiting_for_author_h > pr.waiting_for_reviewer_h * 2
        ]
        if not trap_prs:
            return None

        return Insight(
            category="Bottleneck",
            title="Rework Trap",
            description=f"{len(trap_prs)} PRs spent 2x more time waiting for the author than for reviewers.",
            impact="Indicates potential roadblocks in addressing feedback or complex rework."
        )


class SizeThroughputCorrelationRule:
    def __init__(self, size_limit: int = 300, lifetime_limit_h: float = 16.0):
        self.size_limit = size_limit
        self.lifetime_limit_h = lifetime_limit_h

    def check(self, prs: List[PullRequest]) -> Optional[Insight]:
        large_slow_prs = [
            pr for pr in prs 
            if pr.size > self.size_limit and pr.lifetime_h > self.lifetime_limit_h
        ]
        if not large_slow_prs:
            return None

        return Insight(
            category="Efficiency",
            title="Large PRs Slower Throughput",
            description=f"{len(large_slow_prs)} PRs > {self.size_limit} lines took > {self.lifetime_limit_h} business hours to merge.",
            impact="Empirical evidence that smaller batches improve flow."
        )


class InsightAnalyzer:
    """Analyzes PR data to find patterns and anomalies by running a collection of rules."""

    def __init__(self, rules: Optional[List[AnalyzerRule]] = None):
        self.rules = rules or [
            SlowReviewsRule(),
            LargePRsRule(),
            HighReworkRule(),
            JiraTraceabilityRule(),
            ReworkTrapRule(),
            SizeThroughputCorrelationRule(),
        ]

    def analyze(self, prs: List[PullRequest]) -> List[Insight]:
        """Runs all registered rules and collects valid insights."""
        if not prs:
            return []

        insights: List[Insight] = []
        for rule in self.rules:
            result = rule.check(prs)
            if result:
                insights.append(result)

        return insights
