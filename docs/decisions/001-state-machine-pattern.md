# ADR-001: State Machine over Message Queue

## Status

Accepted

## Context

We need to coordinate multiple agents through a pipeline. Two primary patterns exist:

1. **State Machine** - Agents read/write shared state, transitions are explicit
2. **Message Queue** - Agents communicate via async messages

## Decision

Use a state machine pattern with shared `TaskState`.

## Rationale

- **Determinism** - State transitions are explicit and testable
- **Debuggability** - Full state visible at every step via `to_dict()`
- **Simplicity** - No message broker infrastructure needed
- **LangGraph compatibility** - Aligns with LangGraph's graph-based patterns
- **Iteration control** - Natural loop support for revision cycles

## Trade-offs

- Less suitable for truly distributed agents
- Sequential execution (fine for our use case)
- State grows with pipeline length (manageable with cleanup)

## Consequences

- All agents receive and return `TaskState`
- State machine logic lives in the Orchestrator
- Testing requires building state objects (straightforward with dataclass defaults)
