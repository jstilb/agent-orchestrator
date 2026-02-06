"""Review agent that quality-checks the analysis.

Evaluates the analysis for completeness, accuracy, and coherence.
Can request revisions by returning the state to the analyzer.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.state.models import AgentRole, TaskState, TaskStatus


class ReviewerAgent(BaseAgent):
    """Reviews analysis quality and provides feedback."""

    QUALITY_CHECKS = [
        ("length", lambda a: len(a) > 50, "Analysis is too short"),
        ("has_conclusion", lambda a: "conclusion" in a.lower(), "Missing conclusion"),
        ("has_points", lambda a: "-" in a or "1." in a, "Missing structured points"),
    ]

    def __init__(self, mock: bool = True, approval_threshold: float = 0.6) -> None:
        super().__init__(role=AgentRole.REVIEWER, mock=mock)
        self.approval_threshold = approval_threshold

    def process(self, state: TaskState) -> TaskState:
        """Review the analysis and decide: approve or request revision."""
        state.status = TaskStatus.REVIEWING
        self._add_message(state, "Reviewing analysis quality")

        if not state.analysis:
            state.review_notes.append("REJECT: No analysis provided")
            state.status = TaskStatus.FAILED
            state.error = "No analysis to review"
            return state

        score, notes = self._evaluate(state.analysis)
        state.review_notes.extend(notes)

        if score >= self.approval_threshold:
            state.status = TaskStatus.COMPLETE
            state.final_output = state.analysis
            self._add_message(state, f"Approved (score: {score:.2f})")
        elif state.iteration_count >= state.max_iterations:
            state.status = TaskStatus.COMPLETE
            state.final_output = state.analysis
            self._add_message(state, f"Max iterations reached, accepting (score: {score:.2f})")
        else:
            state.status = TaskStatus.ANALYZING  # Send back to analyzer
            state.iteration_count += 1
            self._add_message(state, f"Revision requested (score: {score:.2f}, iteration {state.iteration_count})")

        return state

    def _evaluate(self, analysis: str) -> tuple[float, list[str]]:
        """Evaluate analysis quality using heuristic checks."""
        passed = 0
        notes: list[str] = []

        for name, check, failure_msg in self.QUALITY_CHECKS:
            if check(analysis):
                passed += 1
                notes.append(f"PASS: {name}")
            else:
                notes.append(f"FAIL: {name} - {failure_msg}")

        score = passed / len(self.QUALITY_CHECKS) if self.QUALITY_CHECKS else 0.0
        return score, notes
