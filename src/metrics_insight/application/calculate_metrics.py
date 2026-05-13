from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from metrics_insight.domain.pull_request import PullRequest
from metrics_insight.domain.repository_interfaces import (
    GitHubRepository, 
    MetricsExporter, 
    ExportResult, 
    SentimentAnalyzer, 
    RootCauseAnalyzer,
    PredictiveAnalyzer
)
from metrics_insight.domain.analyzer import InsightAnalyzer, Insight
from metrics_insight.domain.metrics_service import MetricsService, GroupMetrics
from metrics_insight.domain.sentiment_service import SentimentService


@dataclass(frozen=True)
class PRPrediction:
    """Prediction for a specific PR."""
    number: int
    title: str
    estimated_duration_h: float
    rework_risk_label: str
    risk_factors: List[str]


@dataclass(frozen=True)
class CalculationResult:
    """Consolidated result of a metrics calculation."""
    repo_name: str
    start_date: datetime
    end_date: datetime
    prs: List[PullRequest]
    team_metrics: GroupMetrics
    individual_metrics: List[GroupMetrics]
    label_metrics: List[GroupMetrics]
    insights: List[Insight]
    sentiment: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[str] = None
    predictions: List[PRPrediction] = None


class CalculateMetrics:
    """Use case to fetch, calculate and export metrics."""

    def __init__(self, 
                 github_repo: GitHubRepository, 
                 exporter: MetricsExporter, 
                 sentiment_analyzer: Optional[SentimentAnalyzer] = None,
                 root_cause_analyzer: Optional[RootCauseAnalyzer] = None,
                 predictive_analyzer: Optional[PredictiveAnalyzer] = None):
        self.github_repo = github_repo
        self.exporter = exporter
        self.analyzer = InsightAnalyzer()
        self.metrics_service = MetricsService()
        self.sentiment_service = SentimentService(sentiment_analyzer) if sentiment_analyzer else None
        self.root_cause_analyzer = root_cause_analyzer
        self.predictive_analyzer = predictive_analyzer

    def execute(self, repo_name: str, start_date: datetime, end_date: datetime, output_path: str) -> CalculationResult:
        prs = self.github_repo.get_pull_requests(repo_name, start_date, end_date)

        team_metrics = self.metrics_service.calculate_team_metrics(prs)
        individual_metrics = self.metrics_service.calculate_individual_metrics(prs)
        label_metrics = self.metrics_service.calculate_label_metrics(prs)

        insights = self.analyzer.analyze(prs)
        
        sentiment_result = None
        if self.sentiment_service:
            sentiment_result = self.sentiment_service.analyze_team_sentiment(prs)

        ai_analysis = None
        if self.root_cause_analyzer:
            ai_analysis = self.root_cause_analyzer.suggest_root_causes(
                team_metrics.to_dict(), 
                insights
            )

        predictions = []
        if self.predictive_analyzer and prs:
            history_data = [team_metrics.to_dict()]
            for pr in prs[:3]:
                pr_data = {
                    "number": pr.number,
                    "title": pr.title,
                    "size": pr.size,
                    "author": pr.author,
                    "labels": pr.labels
                }
                pred_raw = self.predictive_analyzer.predict_pr_outcomes(pr_data, history_data)
                predictions.append(PRPrediction(
                    number=pr.number,
                    title=pr.title,
                    estimated_duration_h=pred_raw.get("estimated_duration_h", 0.0),
                    rework_risk_label=pred_raw.get("rework_risk_label", "Unknown"),
                    risk_factors=pred_raw.get("risk_factors", [])
                ))

        result = CalculationResult(
            repo_name=repo_name,
            start_date=start_date,
            end_date=end_date,
            prs=prs,
            team_metrics=team_metrics,
            individual_metrics=individual_metrics,
            label_metrics=label_metrics,
            insights=insights,
            sentiment=sentiment_result,
            ai_analysis=ai_analysis,
            predictions=predictions
        )

        export_data = ExportResult(
            repo_name=result.repo_name,
            start_date=result.start_date,
            end_date=result.end_date,
            prs=result.prs,
            team_metrics=result.team_metrics.to_dict(),
            individual_metrics=[m.to_dict() for m in result.individual_metrics],
            label_metrics=[m.to_dict() for m in result.label_metrics]
        )
        self.exporter.export(export_data, output_path)

        return result
