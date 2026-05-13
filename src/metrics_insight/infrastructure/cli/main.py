import click
import os
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from metrics_insight.application.calculate_metrics import PRPrediction
from metrics_insight.domain.analyzer import Insight
from metrics_insight.domain.metrics_service import GroupMetrics
from dotenv import load_dotenv

from metrics_insight.bootstrap import bootstrap

load_dotenv()
console = Console()

try:
    _container = bootstrap()
except Exception:
    _container = None

def display_predictions(predictions: List[PRPrediction]) -> None:
    """Displays AI predictions for PRs."""
    if not predictions:
        return
        
    table = Table(title="[bold blue]AI Predictive Analysis: Recent PR Risks[/]")
    table.add_column("PR #", style="cyan")
    table.add_column("Title", style="dim")
    table.add_column("Est. Duration (h)", justify="right")
    table.add_column("Rework Risk", justify="center")
    table.add_column("Risk Factors", style="italic")

    for pred in predictions:
        risk_color = "green"
        if pred.rework_risk_label == "High":
            risk_color = "red"
        elif pred.rework_risk_label == "Medium":
            risk_color = "yellow"

        table.add_row(
            f"#{pred.number}",
            pred.title[:40],
            f"{pred.estimated_duration_h:.1f}h",
            f"[{risk_color}]{pred.rework_risk_label}[/]",
            ", ".join(pred.risk_factors)
        )

    console.print(table)

def display_ai_analysis(analysis: Optional[str]) -> None:
    """Displays AI-driven root cause analysis."""
    if not analysis:
        return
        
    console.print(Panel(
        analysis,
        title="[bold blue]AI Root Cause Analysis (Gemini)[/]",
        expand=False,
        border_style="blue"
    ))

def display_sentiment(sentiment: Optional[Dict[str, Any]]) -> None:
    """Displays sentiment analysis results."""
    if not sentiment:
        return
        
    color = "green"
    if sentiment.get("friction_detected"):
        color = "bold red"
    elif sentiment.get("sentiment_label") == "Negative":
        color = "red"
    elif sentiment.get("sentiment_label") == "Neutral":
        color = "yellow"

    score = sentiment.get("sentiment_score", 0.0)
    label = sentiment.get("sentiment_label", "Unknown")
    summary = sentiment.get("summary", "")
    
    console.print(Panel(
        f"[bold]Overall Sentiment:[/] [{color}]{label} ({score:.2f})[/]\n"
        f"[bold]Friction Detected:[/] {'[bold red]YES[/]' if sentiment.get('friction_detected') else '[green]No[/]'}\n\n"
        f"{summary}",
        title="[bold blue]AI Team Sentiment Analysis (Gemini)[/]",
        expand=False
    ))

def display_insights(insights: List[Insight]) -> None:
    """Displays intelligent analysis insights."""
    if not insights:
        return
        
    console.print("\n[bold]Intelligent Analysis Insights:[/]")
    for insight in insights:
        color = "red" if insight.category in ["Bottleneck", "Quality Risk"] else "green"
        console.print(Panel(
            f"[bold]{insight.description}[/]\n[italic]Impact: {insight.impact}[/]",
            title=f"[{color}]{insight.category}: {insight.title}[/]",
            expand=False
        ))

def display_summary_table(team_metrics: GroupMetrics, repo: str) -> None:
    """Displays a summary table of the team's metrics."""
    table = Table(title=f"Team Summary: {repo}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Total PRs", str(team_metrics.total_prs))
    table.add_row("Jira Coverage", f"{team_metrics.jira_percentage:.1f}%")
    
    if team_metrics.metrics.get("pr_size"):
        table.add_row("Avg PR Size", f"{team_metrics.metrics['pr_size'].average:.1f}")
    if team_metrics.metrics.get("pr_lifetime_h"):
        table.add_row("Avg Lifetime (h)", f"{team_metrics.metrics['pr_lifetime_h'].average:.1f}")
    if team_metrics.metrics.get("time_to_first_review_h"):
        table.add_row("Avg 1st Review (h)", f"{team_metrics.metrics['time_to_first_review_h'].average:.1f}")

    console.print(table)

def display_comparison_table(results: List[Dict[str, Any]], repo: str) -> None:
    """Displays comparison table across sprints."""
    table = Table(title=f"Sprint Comparison: {repo}")
    table.add_column("Sprint", style="cyan")
    table.add_column("Start Date", style="dim")
    table.add_column("End Date", style="dim")
    table.add_column("Total PRs", justify="right")
    table.add_column("Avg Size", justify="right")
    table.add_column("Avg Lifetime (h)", justify="right")
    table.add_column("Avg 1st Review (h)", justify="right")

    for res in results:
        # YYYY-MM-DD
        s_date = res["start_date"][:10]
        e_date = res["end_date"][:10]
        table.add_row(
            res["label"],
            s_date,
            e_date,
            str(res["total_prs"]),
            f"{res['pr_size_avg']:.1f}",
            f"{res['pr_lifetime_h_avg']:.1f}",
            f"{res['time_to_first_review_h_avg']:.1f}"
        )

    console.print(table)


def display_workflow_metrics(results: Dict[str, Any], repo: str) -> None:
    """Displays GitHub Actions execution time metrics."""
    table = Table(title=f"GitHub Actions Metrics: {repo}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Runs", str(results["total_runs"]))
    table.add_row("Completed Runs", str(results["completed_runs"]))
    table.add_row("Avg Duration", f"{results['avg_duration_seconds'] / 60:.2f} min")
    
    success_color = "green" if results["success_rate"] > 90 else "yellow" if results["success_rate"] > 70 else "red"
    table.add_row("Success Rate", f"[{success_color}]{results['success_rate']:.1f}%[/]")

    console.print(table)

    if results["runs"]:
        runs_table = Table(title="Top 5 Longest Workflow Runs")
        runs_table.add_column("Name", style="cyan")
        runs_table.add_column("Conclusion", justify="center")
        runs_table.add_column("Duration", justify="right")
        runs_table.add_column("Date", style="dim")

        sorted_runs = sorted(
            [r for r in results["runs"] if r["duration_seconds"] > 0],
            key=lambda x: x["duration_seconds"],
            reverse=True
        )[:5]

        for run in sorted_runs:
            conclusion_color = "green" if run["conclusion"] == "success" else "red"
            runs_table.add_row(
                run["name"],
                f"[{conclusion_color}]{run['conclusion'] or 'N/A'}[/]",
                f"{run['duration_seconds'] / 60:.2f} min",
                run["created_at"][:10]
            )
        console.print(runs_table)


@click.group()
def cli() -> None:
    """Metrics Insight: Engineering metrics from GitHub and Jira."""
    pass

@cli.command()
@click.option("--repo", required=True, help="GitHub repository (owner/repo)")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
@click.option("--output", default="./output", help="Output directory")
def fetch(repo: str, start: str, end: str, output: str) -> None:
    """Fetch metrics from GitHub and save to CSV."""
    if not _container:
        console.print("[bold red]Error:[/] Bootstrap failed. Check GITHUB_TOKEN.")
        return

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        console.print("[bold red]Error:[/] Invalid date format. Use YYYY-MM-DD.")
        return

    console.print(f"Fetching metrics for [bold blue]{repo}[/] from {start} to {end}...")

    if _container.ai_adapter:
        console.print("[dim]AI Analysis enabled (Gemini 1.5 Flash)[/]")

    use_case = _container.get_calculate_metrics()

    start_perf = time.perf_counter()
    result = use_case.execute(repo, start_date, end_date, output)
    end_perf = time.perf_counter()

    duration = end_perf - start_perf
    console.print(f"[bold green]Success![/] Metrics saved to [yellow]{output}[/] (Execution time: {duration:.2f}s)")

    display_summary_table(result.team_metrics, repo)
    display_predictions(result.predictions)
    display_sentiment(result.sentiment)
    display_ai_analysis(result.ai_analysis)
    display_insights(result.insights)

@cli.command()
@click.option("--repo", required=True, help="GitHub repository (owner/repo)")
@click.option("--start", help="Start date (YYYY-MM-DD), default is now minus total sprint duration")
@click.option("--weeks", default=2, type=int, help="Sprint duration in weeks")
@click.option("--sprints", default=4, type=int, help="Number of sprints to compare")
@click.option("--output", default="./output", help="Output directory")
def compare(repo: str, start: str, weeks: int, sprints: int, output: str) -> None:
    """Compare performance across multiple sprints."""
    if not _container:
        console.print("[bold red]Error:[/] Bootstrap failed. Check GITHUB_TOKEN.")
        return

    if start:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            console.print("[bold red]Error:[/] Invalid date format. Use YYYY-MM-DD.")
            return
    else:
        start_date = (datetime.now(timezone.utc) - timedelta(weeks=weeks * sprints))

    console.print(f"Comparing [bold blue]{sprints}[/] sprints ([yellow]{weeks} weeks each[/]) starting from {start_date.strftime('%Y-%m-%d')} for {repo}...")

    use_case = _container.get_compare_sprints()
    results = use_case.execute(repo, start_date, weeks, sprints, output)

    if not results:
        console.print("[yellow]No data found for the specified sprints.[/]")
        return

    display_comparison_table(results, repo)
    
    safe_repo = repo.replace("/", "_").replace("..", "_")
    base_dir = os.path.abspath(output)
    repo_dir = os.path.join(base_dir, safe_repo)
    
    try:
        os.makedirs(repo_dir, exist_ok=True)
        csv_path = os.path.join(repo_dir, "sprint_comparison.csv")
        pd.DataFrame(results).to_csv(csv_path, index=False)
        console.print(f"\n[bold green]Comparison saved to:[/] [yellow]{csv_path}[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] Could not save comparison: {e}")

@cli.command()
@click.option("--repo", required=True, help="GitHub repository (owner/repo)")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
def actions(repo: str, start: str, end: str) -> None:
    """Get GitHub Actions execution time metrics."""
    if not _container:
        console.print("[bold red]Error:[/] Bootstrap failed. Check GITHUB_TOKEN.")
        return

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        console.print("[bold red]Error:[/] Invalid date format. Use YYYY-MM-DD.")
        return

    console.print(f"Fetching Actions metrics for [bold blue]{repo}[/] from {start} to {end}...")

    use_case = _container.get_workflow_metrics()
    results = use_case.execute(repo, start_date, end_date)

    if results["total_runs"] == 0:
        console.print("[yellow]No workflow runs found for the specified period.[/]")
        return

    display_workflow_metrics(results, repo)



@cli.command()
def version() -> None:
    """Show version and exit."""
    console.print("[bold blue]Metrics Insight[/] [green]v0.1.0[/]")

if __name__ == "__main__":
    cli()
