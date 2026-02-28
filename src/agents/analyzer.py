"""Analysis agent that synthesizes research findings.

Takes research results and produces a structured analysis.
In mock mode, generates deterministic analysis text.
In production mode, uses the Anthropic API for LLM synthesis.
"""

from __future__ import annotations

import os

from src.agents.base import BaseAgent
from src.state.models import AgentRole, TaskState, TaskStatus


class AnalyzerAgent(BaseAgent):
    """Analyzes research results and produces synthesis."""

    def __init__(self, mock: bool | None = None) -> None:
        if mock is None:
            mock = os.environ.get("ANTHROPIC_API_KEY") is None
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
        """Production analysis using the Anthropic API.

        Requires ANTHROPIC_API_KEY environment variable.
        Falls back to mock if key is absent.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return self._mock_analyze(query, results)

        try:
            import anthropic  # type: ignore[import-untyped]
            client = anthropic.Anthropic(api_key=api_key)
            findings_text = "\n".join(f"- {r}" for r in results)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Analyze these research findings about '{query}':\n\n"
                            f"{findings_text}\n\n"
                            "Provide a structured analysis with: Key Points (bullet list) "
                            "and a Conclusion sentence."
                        ),
                    }
                ],
            )
            return message.content[0].text if message.content else self._mock_analyze(query, results)
        except Exception as exc:  # noqa: BLE001
            return self._mock_analyze(query, results) + f"\n\n[Production error: {exc}]"
