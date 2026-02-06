"""Basic pipeline example - run the full agent orchestrator."""

from src.orchestrator import AgentOrchestrator, OrchestratorConfig


def main() -> None:
    # Create orchestrator in mock mode (no API keys needed)
    config = OrchestratorConfig(
        mock=True,
        max_iterations=3,
        approval_threshold=0.6,
    )
    orchestrator = AgentOrchestrator(config)

    # Run a query
    result = orchestrator.run("What are the key trends in AI safety?")

    # Print results
    print(f"Query: {result.query}")
    print(f"Status: {result.status.value}")
    print(f"Iterations: {result.iteration_count}")
    print(f"Messages: {len(result.messages)}")
    print()

    print("Research Results:")
    for i, finding in enumerate(result.research_results, 1):
        print(f"  {i}. {finding}")
    print()

    print("Analysis:")
    print(f"  {result.analysis[:300]}...")
    print()

    print("Review Notes:")
    for note in result.review_notes:
        print(f"  - {note}")
    print()

    print("Final Output:")
    print(f"  {result.final_output[:300]}...")


if __name__ == "__main__":
    main()
