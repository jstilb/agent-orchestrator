"""CLI for the agent orchestrator."""

from __future__ import annotations

import argparse
import json
import sys

from src.orchestrator import AgentOrchestrator, OrchestratorConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run agents on a query")
    run_parser.add_argument("query", help="Query to process")
    run_parser.add_argument("--max-iterations", type=int, default=3)

    subparsers.add_parser("demo", help="Run demo")
    subparsers.add_parser("graph", help="Show graph structure")

    args = parser.parse_args()

    if args.command == "run":
        run_query(args.query, args.max_iterations)
    elif args.command == "demo":
        run_demo()
    elif args.command == "graph":
        show_graph()
    else:
        parser.print_help()
        sys.exit(1)


def run_query(query: str, max_iterations: int) -> None:
    config = OrchestratorConfig(mock=True, max_iterations=max_iterations)
    orchestrator = AgentOrchestrator(config)
    result = orchestrator.run(query)
    print(json.dumps(result.to_dict(), indent=2))


def run_demo() -> None:
    print("=" * 60)
    print("Agent Orchestrator - Demo")
    print("=" * 60)

    config = OrchestratorConfig(mock=True)
    orchestrator = AgentOrchestrator(config)

    queries = [
        "What are the latest advances in AI safety?",
        "How does quantum computing work?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        result = orchestrator.run(query)
        print(f"Status: {result.status.value}")
        print(f"Iterations: {result.iteration_count}")
        print(f"Messages: {len(result.messages)}")
        print(f"Output: {result.final_output[:200]}...")
        print()

    print("=" * 60)


def show_graph() -> None:
    orchestrator = AgentOrchestrator()
    graph = orchestrator.get_graph_description()
    print(json.dumps(graph, indent=2))


if __name__ == "__main__":
    main()
