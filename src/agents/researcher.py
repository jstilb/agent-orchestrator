"""Research agent that gathers information on a topic.

In mock mode, returns deterministic research results.
In production mode, uses the Anthropic API to generate real research.
"""

from __future__ import annotations

import hashlib
import os

from src.agents.base import BaseAgent
from src.state.models import AgentRole, TaskState, TaskStatus


class ResearchAgent(BaseAgent):
    """Gathers research data for a given query."""

    MOCK_RESULTS = {
        "default": [
            "Research finding 1: The topic has significant implications across multiple domains.",
            "Research finding 2: Recent studies show measurable improvements in key metrics.",
            "Research finding 3: Expert consensus supports a multi-faceted approach.",
        ],
        "technology": [
            "Technology research: Latest benchmarks show 40% improvement in performance.",
            "Technology research: Adoption rates have doubled in the past year.",
            "Technology research: Three competing approaches have emerged as frontrunners.",
        ],
        "science": [
            "Scientific research: Peer-reviewed studies confirm the hypothesis.",
            "Scientific research: Reproducibility rate exceeds 85% across labs.",
            "Scientific research: New methodology enables faster experimentation.",
        ],
    }

    def __init__(self, mock: bool | None = None) -> None:
        # Auto-detect mock mode: use production if ANTHROPIC_API_KEY is set, else mock
        if mock is None:
            mock = os.environ.get("ANTHROPIC_API_KEY") is None
        super().__init__(role=AgentRole.RESEARCHER, mock=mock)

    def process(self, state: TaskState) -> TaskState:
        """Research the query and populate research_results."""
        state.status = TaskStatus.RESEARCHING
        self._add_message(state, f"Starting research on: {state.query}")

        if self.mock:
            results = self._mock_research(state.query)
        else:
            results = self._production_research(state.query)

        state.research_results = results
        self._add_message(state, f"Found {len(results)} research results")
        return state

    def _mock_research(self, query: str) -> list[str]:
        """Generate deterministic mock research results."""
        query_lower = query.lower()

        # Select result set based on query content
        for category, results in self.MOCK_RESULTS.items():
            if category in query_lower:
                return [r.replace("research:", f"research on '{query}':") for r in results]

        # Default with query-specific variation
        h = int(hashlib.md5(query.encode()).hexdigest()[:4], 16)
        base = self.MOCK_RESULTS["default"]
        return [
            f"Finding on '{query}': {base[i % len(base)].split(': ', 1)[1]}"
            for i in range(3)
        ]

    def _production_research(self, query: str) -> list[str]:
        """Production research using the Anthropic API.

        Requires ANTHROPIC_API_KEY environment variable.
        Falls back to mock if key is absent.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return self._mock_research(query)

        try:
            import anthropic  # type: ignore[import-untyped]
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Provide 3 concise research findings about: {query}\n"
                            "Format as a numbered list. Each item should be one sentence."
                        ),
                    }
                ],
            )
            raw = message.content[0].text if message.content else ""
            lines = [line.strip() for line in raw.splitlines() if line.strip()]
            # Extract lines that look like findings (numbered or bullet)
            findings = [
                line.lstrip("0123456789.-) ").strip()
                for line in lines
                if line and line[0].isdigit() or line.startswith("-")
            ]
            return findings[:3] if findings else [raw[:200]]
        except Exception as exc:  # noqa: BLE001
            return [f"Research error (falling back): {exc}", *self._mock_research(query)[:2]]
