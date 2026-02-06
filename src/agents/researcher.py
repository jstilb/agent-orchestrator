"""Research agent that gathers information on a topic.

In mock mode, returns deterministic research results.
In production mode, would use web search and document retrieval.
"""

from __future__ import annotations

import hashlib

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

    def __init__(self, mock: bool = True) -> None:
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
        """Production research - would use actual search APIs."""
        return [f"Real research result for: {query}"]
