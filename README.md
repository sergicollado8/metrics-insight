# Metrics Insight

`Metrics Insight` is an engineering productivity tool designed to analyze team performance through GitHub data (and soon Jira). It follows **Hexagonal Architecture** and uses **Business Hours (08:00 - 20:00, Mon-Fri, UTC)** for all calculations.

## Key Features
- **Fetch Metrics:** Calculate PR Size, Life Time, Time to 1st Human Review, and Rework for a specific date range.
- **Sprint Comparison:** Track team trajectories over multiple time windows (sprint-by-sprint analysis).
- **GitHub Actions Metrics:** Analyze CI/CD performance (duration, success rate, and bottlenecks).
- **Output Grouping:** Automatic CSV organization in repository-specific subfolders (`output/{owner}_{repo}/`).

## Prerequisites
- **Python 3.13+**
- **GitHub Personal Access Token** (classic or fine-grained) with `repo` scope.
- **Google Gemini API Key** (optional, for AI-driven features).

> [!IMPORTANT]
> **Privacy Notice:** When `GEMINI_API_KEY` is provided, this tool sends Pull Request metadata, titles, descriptions, and human review comments to Google's Gemini API for sentiment analysis and root cause identification. If you are working in a privacy-sensitive environment or with proprietary code where third-party AI processing is restricted, omit the `GEMINI_API_KEY` to keep all processing local to your machine.

## Installation & Setup

### Using Docker (Recommended)
The easiest way to run `Metrics Insight` is using Docker. This ensures all dependencies and Python versions are correctly configured.

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd metrics_insight
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory (use `.env.template` as a guide):
   ```text
   GITHUB_TOKEN=your_github_token
   GEMINI_API_KEY=your_gemini_api_key  # Optional
   ```

3. **Build the image:**
   ```bash
   make docker-build
   ```

### Local Installation (Development)
If you prefer to run it locally or contribute to the code:
```bash
make install
```

## Usage

The tool provides several commands. When using Docker, use `make docker-run ARGS="<command> <options>"` to ensure your `.env` is loaded and your `output/` folder is synced.

### 1. Fetch Basic Metrics
Extracts PR metrics and saves them to CSV. Also performs AI analysis if a Gemini key is provided.
```bash
make docker-run ARGS="fetch --repo owner/repo --start 2024-01-01 --end 2024-03-31"
```

### 2. Compare Sprints (Trajectories)
Compares multiple time windows to see if the team's performance is improving.
```bash
make docker-run ARGS="compare --repo owner/repo --start 2024-01-01 --weeks 2 --sprints 4"
```

### 3. Analyze GitHub Actions
Analyzes workflow execution times and success rates.
```bash
make docker-run ARGS="actions --repo owner/repo --start 2024-01-01 --end 2024-03-31"
```

---

*Note: For local execution without Docker, replace `make docker-run ARGS="..."` with `make <command> ARGS="..."` (e.g., `make run ARGS="..."` for fetching).*

## Metrics Definitions
- **PR Size:** Total lines changed (additions + deletions).
- **PR Life Time:** Duration from creation to merge/close (Business Hours).
- **Time to 1st Review:** Duration from creation to the first human review (Business Hours).
- **Rework:** Number of commits after the first human review (excluding merges).
- **Success Rate (Actions):** Percentage of workflow runs that ended in `success`.

## Project Structure
The project follows a strict **Hexagonal Architecture** (Ports & Adapters):

- `src/metrics_insight/domain/`: Pure business logic, entities, and repository interfaces (Ports).
- `src/metrics_insight/application/`: Use cases that orchestrate domain logic.
- `src/metrics_insight/infrastructure/`:
  - `github/`: Adapter for GitHub API (using PyGithub).
  - `csv/`: Adapter for CSV exporting.
  - `cli/`: Command-line interface (using Click and Rich).
  - `ai/`: Adapter for Google Gemini (Generative AI).
- `tests/`: 
  - `unit/`: Fast tests for domain and application logic.
  - `integration/`: Tests for infrastructure adapters.
  - `acceptance/`: End-to-end tool validation.

## Development & Quality Standards
**Mandate:** Every new feature and logic change MUST include associated tests.

### Commands
- **Test:** `make test` (runs pytest)
- **Lint:** `make lint` (runs ruff and mypy)
- **Build:** `make build` (creates local package)
- **Docker:** `make docker-build` and `make docker-run`

## License
MIT
