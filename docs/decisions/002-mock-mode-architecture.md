# ADR-002: Mock Mode Architecture

## Status

Accepted

## Context

The system needs to work both as a portfolio demo (no API keys) and as a production agent pipeline. We need a clean way to switch between mock and real implementations.

## Decision

Use a `mock` boolean flag at the agent level, with mock being the default.

## Rationale

- **Zero configuration** - Default mock mode works out of the box
- **Deterministic testing** - Mock results are predictable
- **Simple interface** - Single flag, no factory complexity
- **Incremental adoption** - Switch one agent at a time to production

## Alternatives Considered

1. **Abstract provider interface** - More flexible but over-engineered for 3 agents
2. **Environment-based switching** - Less explicit, harder to test
3. **Separate mock classes** - More code duplication

## Consequences

- Each agent has `_mock_*` and `_production_*` methods
- Tests always use `mock=True` for reliability
- Production mode is opt-in via configuration
- Demo mode (CLI) defaults to mock
