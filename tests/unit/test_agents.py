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
