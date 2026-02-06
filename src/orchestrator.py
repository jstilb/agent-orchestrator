"""Agent orchestrator using state machine coordination.

Implements a directed graph where agents are nodes and
transitions are edges. The graph follows:

  Research -> Analyze -> Review -> [Complete | Analyze (revision)]

Uses LangGraph patterns but works without LangGraph dependency
for testing (pure Python state machine fallback).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from src.agents.analyzer import AnalyzerAgent
from src.agents.researcher import ResearchAgent
from src.agents.reviewer import ReviewerAgent
from src.state.models import TaskState, TaskStatus


@dataclass
class OrchestratorConfig:
    """Configuration for the agent orchestrator."""
    mock: bool = True
    max_iterations: int = 3
    approval_threshold: float = 0.6


class AgentOrchestrator:
    """Coordinates multiple agents through a state machine.

    The orchestrator manages the flow:
    1. Researcher gathers information
    2. Analyzer synthesizes findings
    3. Reviewer evaluates quality
    4. If rejected and under iteration limit -> back to Analyzer
    5. If approved or max iterations -> complete

    Usage:
        orchestrator = AgentOrchestrator(OrchestratorConfig(mock=True))
        result = orchestrator.run("What is quantum computing?")
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None) -> None:
        self.config = config or OrchestratorConfig()
        self.researcher = ResearchAgent(mock=self.config.mock)
        self.analyzer = AnalyzerAgent(mock=self.config.mock)
        self.reviewer = ReviewerAgent(
            mock=self.config.mock,
            approval_threshold=self.config.approval_threshold,
        )

    def run(self, query: str) -> TaskState:
        """Execute the full agent pipeline for a query.

        Returns the final TaskState with all intermediate results.
        """
        state = TaskState(
            query=query,
            max_iterations=self.config.max_iterations,
        )

        # Step 1: Research
        state = self.researcher.process(state)
        if state.status == TaskStatus.FAILED:
            return state

        # Step 2-3: Analyze and Review loop
        while state.status != TaskStatus.COMPLETE and state.status != TaskStatus.FAILED:
            # Analyze
            state = self.analyzer.process(state)

            # Review (may send back to analyze)
            state = self.reviewer.process(state)

        return state

    def run_step(self, state: TaskState) -> TaskState:
        """Execute a single step based on current state.

        Useful for step-by-step debugging and visualization.
        """
        if state.status == TaskStatus.PENDING:
            return self.researcher.process(state)
        elif state.status in (TaskStatus.RESEARCHING, TaskStatus.ANALYZING):
            return self.analyzer.process(state)
        elif state.status == TaskStatus.REVIEWING:
            return self.reviewer.process(state)
        return state

    def get_graph_description(self) -> dict[str, list[str]]:
        """Return a description of the agent graph structure."""
        return {
            "nodes": ["researcher", "analyzer", "reviewer"],
            "edges": [
                "START -> researcher",
                "researcher -> analyzer",
                "analyzer -> reviewer",
                "reviewer -> analyzer (revision)",
                "reviewer -> END (approved)",
            ],
        }
