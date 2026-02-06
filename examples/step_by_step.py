"""Step-by-step execution example - run one agent at a time."""

import json

from src.orchestrator import AgentOrchestrator, OrchestratorConfig
from src.state.models import TaskState, TaskStatus


def main() -> None:
    # Create orchestrator
    orchestrator = AgentOrchestrator(OrchestratorConfig(mock=True))

    # Create initial state
    state = TaskState(query="How does quantum computing work?")
    print(f"Initial status: {state.status.value}")
    print()

    # Step 1: Research
    state = orchestrator.run_step(state)
    print(f"After research: {state.status.value}")
    print(f"  Findings: {len(state.research_results)}")
    for r in state.research_results:
        print(f"    - {r[:80]}...")
    print()

    # Step 2: Analyze (manually trigger since status is RESEARCHING)
    state = orchestrator.run_step(state)
    print(f"After analysis: {state.status.value}")
    print(f"  Analysis length: {len(state.analysis)} chars")
    print(f"  Preview: {state.analysis[:100]}...")
    print()

    # Step 3: Review
    state.status = TaskStatus.REVIEWING  # Manually advance for step mode
    state = orchestrator.run_step(state)
    print(f"After review: {state.status.value}")
    print(f"  Review notes: {state.review_notes}")
    print()

    # Show full state as JSON
    print("Full state (JSON):")
    print(json.dumps(state.to_dict(), indent=2))

    # Show graph structure
    print("\nGraph structure:")
    print(json.dumps(orchestrator.get_graph_description(), indent=2))


if __name__ == "__main__":
    main()
