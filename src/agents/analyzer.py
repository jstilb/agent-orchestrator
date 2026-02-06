"""Analysis agent that synthesizes research findings.

Takes research results and produces a structured analysis.
In mock mode, generates deterministic analysis text.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.state.models import AgentRole, TaskState, TaskStatus


class AnalyzerAgent(BaseAgent):
    """Analyzes research results and produces synthesis."""

    def __init__(self, mock: bool = True) -> None:
        super().__init__(role=AgentRole.ANALYZER, mock=mock)

    def process(self, state: TaskState) -> TaskState:
        """Analyze research results and produce synthesis."""
        state.status = TaskStatus.ANALYZING
        self._add_message(state, f"Analyzing {len(state.research_results)} research findings")

        if not state.research_results:
            state.analysis = "No research results available for analysis."
            self._add_message(state, "Warning: No research data to analyze")
            return state

        if self.mock:
            state.analysis = self._mock_analyze(state.query, state.research_results)
        else:
            state.analysis = self._production_analyze(state.query, state.research_results)

        self._add_message(state, f"Analysis complete ({len(state.analysis)} chars)")
        return state

    def _mock_analyze(self, query: str, results: list[str]) -> str:
        """Generate mock analysis from research results."""
        key_points = [r.split(": ", 1)[-1] if ": " in r else r for r in results]

        return (
            f"Analysis of '{query}':\n\n"
            f"Summary: Based on {len(results)} research findings, several key themes emerge.\n\n"
            f"Key Points:\n"
            + "\n".join(f"- {point}" for point in key_points)
            + f"\n\nConclusion: The evidence suggests a comprehensive approach to {query} "
            f"that addresses multiple dimensions of the problem."
        )

    def _production_analyze(self, query: str, results: list[str]) -> str:
        """Production analysis - would use LLM for synthesis."""
        return f"Production analysis of {query} based on {len(results)} sources."
