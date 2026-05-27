import os
import tempfile
import pandas as pd
from datetime import datetime, timezone
from metrics_insight.domain.pull_request import PullRequest
from metrics_insight.domain.repository_interfaces import ExportResult
from metrics_insight.infrastructure.csv.csv_exporter import CSVExporter

def test_save_raw_pull_requests_includes_closed_and_merged_status():
    """Verify that raw_prs.csv includes closed_at and is_merged columns."""
    t1 = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    
    prs = [
        PullRequest(
            number=1, title="Merged", author="alice", 
            created_at=t1, merged_at=t2, closed_at=t2, additions=100
        ),
        PullRequest(
            number=2, title="Closed", author="bob", 
            created_at=t1, closed_at=t2, additions=200
        )
    ]
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        exporter = CSVExporter()
        result = ExportResult(
            repo_name="test/repo",
            start_date=t1,
            end_date=t2,
            prs=prs,
            team_metrics={"label": "Team"},
            individual_metrics=[],
            label_metrics=[]
        )
        
        exporter.export(result, tmp_dir)
        
        safe_repo = "test_repo"
        file_name = f"20260401_20260401_raw_prs.csv"
        csv_path = os.path.join(tmp_dir, safe_repo, file_name)
        
        assert os.path.exists(csv_path)
        df = pd.read_csv(csv_path)
        
        assert "closed_at" in df.columns
        assert "is_merged" in df.columns
        
        merged_row = df[df["number"] == 1].iloc[0]
        closed_row = df[df["number"] == 2].iloc[0]
        
        assert merged_row["is_merged"] == True
        assert closed_row["is_merged"] == False
        assert not pd.isna(closed_row["closed_at"])
        assert pd.isna(closed_row["merged_at"]) or closed_row["merged_at"] == ""
