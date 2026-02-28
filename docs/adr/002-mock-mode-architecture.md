# ADR-002: Mock Mode Architecture

## Status

Accepted

## Context

The agent-orchestrator must function in two distinct operational modes:

1. **Mock mode** — All LLM and external API calls are replaced with deterministic, hard-coded
   results. No `ANTHROPIC_API_KEY` or other credentials are required. This mode is used for:
   - Local development without API keys
   - CI/CD test runs (fast, free, reproducible)
   - Portfolio demo deployments
   - All unit and integration tests

2. **Production mode** — Agents use the Anthropic Python SDK (and potentially other APIs) to
   produce real research, analysis, and review results. Requires `ANTHROPIC_API_KEY`.

The system needs a clean, low-friction mechanism to switch between these modes at agent
instantiation time, without requiring a dependency injection framework or factory classes.

## Decision

Use a `mock` boolean flag on each agent constructor, defaulting to auto-detection based on the
`ANTHROPIC_API_KEY` environment variable:

```python
def __init__(self, mock: bool | None = None) -> None:
    if mock is None:
        mock = os.environ.get("ANTHROPIC_API_KEY") is None
    super().__init__(role=AgentRole.RESEARCHER, mock=mock)
```

- `mock=True` forces mock mode regardless of environment
- `mock=False` forces production mode (will error if key is absent)
- `mock=None` (default) auto-detects: mock when no key is present, production when key is set

Each agent implements two private methods per operation:
- `_mock_<operation>()` — deterministic, no external calls
- `_production_<operation>()` — real API calls, with fallback to mock on error

## Alternatives Considered

1. **Abstract provider interface** (`ResearchProvider`, `AnalysisProvider`) — More flexible for
   swapping providers, but over-engineered for a three-agent system with one LLM target.
2. **Environment-only switching** — Simpler but makes tests that need to force mock mode
   require unsetting environment variables, which is error-prone.
3. **Separate mock subclasses** (`MockResearchAgent`, `ProductionResearchAgent`) — Clean
   separation but doubles the class count and makes orchestrator configuration more complex.

## Rationale

- **Zero configuration** — `mock=None` default means `examples/` scripts work out of the box
  with no environment setup.
- **Explicit override** — Tests always pass `mock=True` explicitly to avoid accidental
  production API calls during CI.
- **Graceful degradation** — `_production_*` methods fall back to mock on exception, ensuring
  demos never crash due to API errors.
- **Incremental production adoption** — A single agent can be switched to production while
  others remain in mock mode during development.

## Consequences

- `OrchestratorConfig.mock` passes through to all three agents
- CI tests always run in mock mode (fast, no cost, no flakiness)
- The `ANTHROPIC_API_KEY` env var is the single control plane for production mode
- `_production_*` methods must handle `ImportError` (if `anthropic` package not installed)
  and network errors gracefully, falling back to mock results rather than crashing
- Examples in `examples/` run to completion without any environment configuration
