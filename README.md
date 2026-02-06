# Agent Orchestrator

Multi-agent orchestration system with state machine coordination and typed message passing. Demonstrates LangGraph-inspired patterns for building reliable, testable agent pipelines.

## Architecture

```
Input Query
    |
    v
[Researcher] -- gathers information
    |
    v
[Analyzer] -- synthesizes findings
    |
    v
[Reviewer] -- evaluates quality
    |           |
    | approve   | request revision
    v           v
 [Complete]  [Analyzer] (loop)
```

Three specialized agents coordinate through a shared `TaskState`:

- **ResearchAgent** - Gathers information from sources (mock or production)
- **AnalyzerAgent** - Synthesizes research into structured analysis
- **ReviewerAgent** - Quality-checks analysis with configurable threshold

The orchestrator manages transitions using a state machine pattern. The reviewer can send work back to the analyzer for revision, up to a configurable iteration limit.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Run demo (no API keys needed)
python -m src.cli demo

# Run a query
python -m src.cli run "What is machine learning?"

# Show agent graph
python -m src.cli graph

# Start API server
uvicorn src.api.app:app --reload
```

## Features

- **State Machine Coordination** - Directed graph with typed transitions
- **Typed Message Passing** - Agents communicate via structured `TaskState`
- **Quality Review Loop** - Reviewer can request revisions up to N iterations
- **Mock Mode** - Full pipeline runs without external dependencies
- **REST API** - FastAPI endpoints for programmatic access
- **CLI Interface** - Command-line tools for demo and queries
- **Serialization** - Full state to_dict/from_dict for persistence

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/run` | Run agent pipeline |
| GET | `/graph` | Get graph structure |

### Example API Call

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"query": "AI safety", "mock": true}'
```

## Project Structure

```
agent-orchestrator/
  src/
    agents/
      base.py          # Abstract base agent
      researcher.py     # Research agent
      analyzer.py       # Analysis agent
      reviewer.py       # Review agent
    state/
      models.py         # TaskState, Message, enums
    api/
      app.py            # FastAPI application
    cli.py              # CLI interface
    orchestrator.py     # State machine coordinator
  tests/
    unit/
      test_state.py     # State model tests
      test_agents.py    # Individual agent tests
      test_cli.py       # CLI tests
    integration/
      test_orchestrator.py  # Full pipeline + API tests
  docs/
    architecture.md     # System architecture
    decisions/          # Architecture Decision Records
  examples/
    basic_pipeline.py   # Basic usage example
    step_by_step.py     # Step-by-step execution
```

## Configuration

```python
from src.orchestrator import AgentOrchestrator, OrchestratorConfig

config = OrchestratorConfig(
    mock=True,              # Use mock providers (no API keys)
    max_iterations=3,       # Max revision cycles
    approval_threshold=0.6, # Quality score threshold
)

orchestrator = AgentOrchestrator(config)
result = orchestrator.run("Your query here")
```

## State Machine

The `TaskState` flows through defined statuses:

| Status | Description |
|--------|-------------|
| `PENDING` | Initial state |
| `RESEARCHING` | Researcher is gathering data |
| `ANALYZING` | Analyzer is synthesizing |
| `REVIEWING` | Reviewer is evaluating |
| `COMPLETE` | Pipeline finished successfully |
| `FAILED` | Pipeline encountered an error |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Type checking
mypy src/

# Linting
ruff check src/ tests/
ruff format src/ tests/

# Build
make build
```

## Design Decisions

See [docs/decisions/](docs/decisions/) for Architecture Decision Records:

- [ADR-001: State Machine over Message Queue](docs/decisions/001-state-machine-pattern.md)
- [ADR-002: Mock Mode Architecture](docs/decisions/002-mock-mode-architecture.md)

## Tech Stack

- **Python 3.11+** with type hints
- **LangGraph patterns** - State machine agent coordination
- **FastAPI** - REST API
- **Pydantic** - Data validation and settings
- **pytest** + hypothesis - Testing with property-based tests
- **ruff** - Linting and formatting
- **mypy** - Static type checking

## License

MIT
