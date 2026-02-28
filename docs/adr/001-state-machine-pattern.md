# ADR-001: State Machine Pattern for Agent Coordination

## Status

Accepted

## Context

We need to coordinate multiple specialized agents (Researcher, Analyzer, Reviewer) through a
multi-stage pipeline. Two primary coordination patterns were considered:

1. **State Machine** — Agents read and write a shared `TaskState` dataclass; transitions between
   pipeline stages are explicit and driven by an orchestrator.
2. **Message Queue** — Agents communicate asynchronously via a message broker (e.g., Redis,
   RabbitMQ), consuming and producing typed messages.

The system must support:
- A revision loop where the Reviewer can send work back to the Analyzer
- Deterministic, reproducible behavior in mock mode for testing and portfolio demos
- A clear audit trail of every agent action via message history
- Integration with LangGraph-style graph execution patterns

## Decision

Use a state machine pattern with a shared `TaskState` dataclass flowing through each agent.

The `TaskStatus` enum defines all legal states:
- `PENDING` → initial state
- `RESEARCHING` → ResearchAgent is active
- `ANALYZING` → AnalyzerAgent is active
- `REVIEWING` → ReviewerAgent is active
- `COMPLETE` → terminal success state
- `FAILED` → terminal error state

The `AgentOrchestrator` drives all transitions. Agents do not call each other directly.

## Rationale

- **Determinism** — State transitions are explicit and testable; given the same input state,
  the same output state is always produced (in mock mode).
- **Debuggability** — `TaskState.to_dict()` serializes the complete state at any point,
  enabling step-by-step replay and inspection.
- **Simplicity** — No message broker infrastructure is needed for development or demos.
- **LangGraph compatibility** — The `process(state) -> state` contract aligns directly with
  LangGraph node function signatures.
- **Iteration control** — The revision loop (Reviewer → Analyzer) is naturally modeled as a
  conditional edge in the state graph, with `max_iterations` as a safety limit.

## Trade-offs

- Sequential execution only (no parallelism across pipeline stages)
- State object grows as the pipeline progresses (bounded by `max_iterations`)
- Less suitable if agents need to run on separate machines (state must be serialized for RPC)

## Consequences

- All agents implement `process(state: TaskState) -> TaskState`
- All state machine logic lives in `AgentOrchestrator`, not in the agents themselves
- `TaskState` must be serializable via `to_dict()` / `from_dict()` for API and WebSocket transport
- Tests build `TaskState` objects directly (straightforward given dataclass defaults)
- Adding a new agent requires adding a new `TaskStatus` value and a new edge in the orchestrator
