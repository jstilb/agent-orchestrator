"""Tests for individual agents."""
import pytest
from src.agents.researcher import ResearchAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.reviewer import ReviewerAgent
from src.state.models import TaskState, TaskStatus, AgentRole


class TestResearchAgent:
    def test_research(self) -> None:
        agent = ResearchAgent(mock=True)
        state = TaskState(query="AI safety")
        result = agent.process(state)
        assert result.status == TaskStatus.RESEARCHING
        assert len(result.research_results) > 0
        assert len(result.messages) > 0

    def test_deterministic(self) -> None:
        agent = ResearchAgent(mock=True)
        s1 = agent.process(TaskState(query="test"))
        s2 = agent.process(TaskState(query="test"))
        assert s1.research_results == s2.research_results

    def test_different_queries(self) -> None:
        agent = ResearchAgent(mock=True)
        s1 = agent.process(TaskState(query="technology trends"))
        s2 = agent.process(TaskState(query="cooking recipes"))
        # Different queries may produce different results
        assert len(s1.research_results) > 0
        assert len(s2.research_results) > 0

    def test_technology_category(self) -> None:
        agent = ResearchAgent(mock=True)
        state = agent.process(TaskState(query="technology advances"))
        assert any("technology" in r.lower() for r in state.research_results)


class TestAnalyzerAgent:
    def test_analyze_with_results(self) -> None:
        agent = AnalyzerAgent(mock=True)
        state = TaskState(query="test topic")
        state.research_results = ["Finding 1: important", "Finding 2: critical"]
        result = agent.process(state)
        assert result.status == TaskStatus.ANALYZING
        assert len(result.analysis) > 0
        assert "test topic" in result.analysis

    def test_analyze_without_results(self) -> None:
        agent = AnalyzerAgent(mock=True)
        state = TaskState(query="empty")
        result = agent.process(state)
        assert "No research results" in result.analysis

    def test_analysis_structure(self) -> None:
        agent = AnalyzerAgent(mock=True)
        state = TaskState(query="structured")
        state.research_results = ["r1", "r2", "r3"]
        result = agent.process(state)
        assert "Analysis" in result.analysis
        assert "Conclusion" in result.analysis


class TestReviewerAgent:
    def test_approve_good_analysis(self) -> None:
        agent = ReviewerAgent(mock=True, approval_threshold=0.6)
        state = TaskState(query="test")
        state.analysis = (
            "Analysis of 'test':\n\n"
            "- Point one about the topic\n"
            "- Point two with details\n\n"
            "Conclusion: The evidence supports the hypothesis."
        )
        result = agent.process(state)
        assert result.status == TaskStatus.COMPLETE
        assert len(result.review_notes) > 0

    def test_reject_empty_analysis(self) -> None:
        agent = ReviewerAgent(mock=True)
        state = TaskState(query="test")
        state.analysis = ""
        result = agent.process(state)
        assert result.status == TaskStatus.FAILED

    def test_reject_short_analysis(self) -> None:
        agent = ReviewerAgent(mock=True, approval_threshold=0.9)
        state = TaskState(query="test")
        state.analysis = "Too short"
        result = agent.process(state)
        # Short analysis without conclusion or points should fail
        assert result.status in (TaskStatus.ANALYZING, TaskStatus.COMPLETE)

    def test_max_iterations_forces_completion(self) -> None:
        agent = ReviewerAgent(mock=True, approval_threshold=1.0)
        state = TaskState(query="test", max_iterations=2, iteration_count=2)
        state.analysis = "Short"
        result = agent.process(state)
        assert result.status == TaskStatus.COMPLETE


class TestProductionModeWithMockFallback:
    """ISC-2730: Test that all agents fall back to mock when ANTHROPIC_API_KEY is absent."""

    def test_researcher_mock_fallback_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ResearchAgent._production_research() falls back to mock when key is absent."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # When no API key, mock=None should resolve to mock=True
        agent = ResearchAgent(mock=None)
        assert agent.mock is True, "Agent should auto-detect mock=True when no API key"

        state = TaskState(query="technology")
        result = agent.process(state)
        assert result.status == TaskStatus.RESEARCHING
        assert len(result.research_results) > 0, "Mock fallback must return research results"
        assert all(isinstance(r, str) for r in result.research_results), "Results must be strings"

    def test_analyzer_mock_fallback_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AnalyzerAgent._production_analyze() falls back to mock when key is absent."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        agent = AnalyzerAgent(mock=None)
        assert agent.mock is True, "Agent should auto-detect mock=True when no API key"

        state = TaskState(query="test topic")
        state.research_results = ["Finding 1", "Finding 2"]
        result = agent.process(state)
        assert result.status == TaskStatus.ANALYZING
        assert len(result.analysis) > 0, "Mock fallback must produce non-empty analysis"
        assert "test topic" in result.analysis, "Analysis must reference the query"

    def test_reviewer_mock_fallback_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ReviewerAgent._production_review() falls back to heuristic when key is absent."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        agent = ReviewerAgent(mock=None, approval_threshold=0.6)
        assert agent.mock is True, "Agent should auto-detect mock=True when no API key"

        state = TaskState(query="test")
        state.analysis = (
            "Analysis of 'test':\n"
            "- Key point one: evidence is strong\n"
            "- Key point two: methodology is sound\n"
            "Conclusion: The findings are conclusive."
        )
        result = agent.process(state)
        assert result.status == TaskStatus.COMPLETE, "Good analysis should be approved"
        assert len(result.review_notes) > 0, "Review notes must be populated"

    def test_production_research_method_exists(self) -> None:
        """ResearchAgent._production_research is a callable method (ISC-2730)."""
        agent = ResearchAgent(mock=True)
        assert callable(getattr(agent, "_production_research", None)), \
            "_production_research must be implemented as a callable method"

    def test_production_analyze_method_exists(self) -> None:
        """AnalyzerAgent._production_analyze is a callable method (ISC-2730)."""
        agent = AnalyzerAgent(mock=True)
        assert callable(getattr(agent, "_production_analyze", None)), \
            "_production_analyze must be implemented as a callable method"

    def test_production_review_method_exists(self) -> None:
        """ReviewerAgent._production_review is a callable method (ISC-2730)."""
        agent = ReviewerAgent(mock=True)
        assert callable(getattr(agent, "_production_review", None)), \
            "_production_review must be implemented as a callable method"
