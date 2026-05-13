import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from metrics_insight.infrastructure.github.github_adapter import PyGithubAdapter


class TestPyGithubAdapterIntegration:
    """
    Integration tests for PyGithubAdapter.
    Mocks the GitHub API client to verify the adapter's orchestration and mapping logic.
    """

    @pytest.fixture
    def mock_github(self):
        with patch("metrics_insight.infrastructure.github.github_adapter.Github") as mock:
            yield mock

    @pytest.fixture
    def adapter(self, mock_github):
        return PyGithubAdapter("fake-token")

    def test_get_pull_requests_filters_and_maps_correctly(self, adapter, mock_github):
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        pr1 = MagicMock()
        pr1.merged_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
        pr1.updated_at = datetime(2024, 1, 16, tzinfo=timezone.utc)
        pr1.number = 101
        pr1.title = "Feature PR"
        pr1.user.login = "author1"
        pr1.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
        pr1.additions = 100
        pr1.deletions = 50
        pr1.labels = [MagicMock(name="bug")]
        pr1.labels[0].name = "bug"
        pr1.get_reviews.return_value = []
        pr1.get_commits.return_value = []
        pr1.get_issue_events.return_value = []
        
        pr2 = MagicMock()
        pr2.merged_at = datetime(2023, 12, 31, tzinfo=timezone.utc)
        pr2.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        mock_repo.get_pulls.return_value = [pr1, pr2]
        
        results = adapter.get_pull_requests("owner/repo", start_date, end_date)
        
        assert len(results) == 1
        assert results[0].number == 101
        assert results[0].title == "Feature PR"
        assert results[0].author == "author1"
        assert "bug" in results[0].labels
        mock_repo.get_pulls.assert_called_once_with(state="closed", sort="updated", direction="desc")

    def test_get_workflow_runs_filters_and_maps_correctly(self, adapter, mock_github):
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 10, tzinfo=timezone.utc)
        
        run1 = MagicMock()
        run1.id = 12345
        run1.name = "CI Pipeline"
        run1.status = "completed"
        run1.conclusion = "success"
        run1.created_at = datetime(2024, 1, 5, tzinfo=timezone.utc)
        run1.updated_at = datetime(2024, 1, 5, 1, 0, tzinfo=timezone.utc)
        run1.run_started_at = datetime(2024, 1, 5, 0, 50, tzinfo=timezone.utc)
        run1.html_url = "http://github.com/run/1"
        
        mock_repo.get_workflow_runs.return_value = [run1]
        
        results = adapter.get_workflow_runs("owner/repo", start_date, end_date)
        
        assert len(results) == 1
        assert results[0].id == 12345
        assert results[0].name == "CI Pipeline"
        assert results[0].duration.total_seconds() == 600  # 10 minutes
        assert results[0].conclusion == "success"

    def test_to_domain_with_reviews_and_rework(self, adapter, mock_github):
        pr = MagicMock()
        pr.number = 1
        pr.title = "Fix JIRA-123"
        pr.body = "This fixes the bug"
        pr.user.login = "dev1"
        pr.created_at = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
        pr.merged_at = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc)
        pr.closed_at = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc)
        pr.additions = 10
        pr.deletions = 5
        pr.labels = []
        
        review = MagicMock()
        review.user.login = "reviewer1"
        review.user.type = "User"
        review.submitted_at = datetime(2024, 1, 1, 14, 0, tzinfo=timezone.utc)
        review.body = "Looks good"
        pr.get_reviews.return_value = [review]
        
        rc1 = MagicMock()
        rc1.user.login = "reviewer1"
        rc1.user.type = "User"
        pr.get_review_comments.return_value = [rc1]
        
        ic1 = MagicMock()
        ic1.user.login = "dev1"
        ic1.user.type = "User"
        bot_c = MagicMock()
        bot_c.user.login = "github-actions"
        bot_c.user.type = "Bot"
        pr.get_issue_comments.return_value = [ic1, bot_c]
        
        commit = MagicMock()
        commit.commit.author.date = datetime(2024, 1, 1, 15, 0, tzinfo=timezone.utc)
        commit.commit.message = "addressing feedback"
        pr.get_commits.return_value = [commit]
        
        pr.get_issue_events.return_value = []
        
        domain_pr = adapter._to_domain(pr)
        
        assert domain_pr.jira_ticket == "JIRA-123"
        assert len(domain_pr.reviews) == 1
        assert domain_pr.commits_after_first_review == 1
        assert domain_pr.rework_count == 1
        assert domain_pr.author_comments_count == 1
        assert domain_pr.other_human_comments_count == 1
        assert domain_pr.bot_comments_count == 1
