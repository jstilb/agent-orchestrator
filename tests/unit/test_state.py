"""Tests for state models."""
import pytest
from hypothesis import given, strategies as st
from src.state.models import TaskState, TaskStatus, AgentRole, Message


class TestTaskState:
    def test_default_state(self) -> None:
        state = TaskState()
        assert state.status == TaskStatus.PENDING
        assert state.messages == []
        assert state.query == ""

    def test_add_message(self) -> None:
        state = TaskState(query="test")
        state.add_message("hello", AgentRole.RESEARCHER)
        assert len(state.messages) == 1
        assert state.messages[0].content == "hello"
        assert state.messages[0].sender == AgentRole.RESEARCHER

    def test_to_dict(self) -> None:
        state = TaskState(query="test query")
        state.add_message("msg", AgentRole.ANALYZER)
        d = state.to_dict()
        assert d["query"] == "test query"
        assert len(d["messages"]) == 1

    def test_from_dict(self) -> None:
        data = {
            "query": "test",
            "status": "analyzing",
            "messages": [{"content": "hi", "sender": "researcher", "timestamp": "t"}],
            "research_results": ["r1"],
            "analysis": "a",
            "review_notes": [],
            "final_output": "",
        }
        state = TaskState.from_dict(data)
        assert state.query == "test"
        assert state.status == TaskStatus.ANALYZING
        assert len(state.messages) == 1

    def test_roundtrip(self) -> None:
        state = TaskState(query="roundtrip")
        state.add_message("msg1", AgentRole.RESEARCHER)
        state.research_results = ["r1", "r2"]
        d = state.to_dict()
        restored = TaskState.from_dict(d)
        assert restored.query == state.query
        assert len(restored.messages) == 1
        assert restored.research_results == ["r1", "r2"]

    @given(st.text(min_size=1, max_size=50))
    def test_query_preserved(self, query: str) -> None:
        state = TaskState(query=query)
        assert state.query == query

    @given(
        query=st.text(min_size=1, max_size=100),
        analysis=st.text(max_size=200),
        research_results=st.lists(st.text(min_size=1, max_size=80), max_size=5),
        final_output=st.text(max_size=200),
        iteration_count=st.integers(min_value=0, max_value=10),
        max_iterations=st.integers(min_value=1, max_value=10),
    )
    def test_serialization_roundtrip(
        self,
        query: str,
        analysis: str,
        research_results: list[str],
        final_output: str,
        iteration_count: int,
        max_iterations: int,
    ) -> None:
        """Property: TaskState serialization round-trip preserves all fields."""
        original = TaskState(
            query=query,
            status=TaskStatus.ANALYZING,
            analysis=analysis,
            research_results=research_results,
            final_output=final_output,
            iteration_count=iteration_count,
            max_iterations=max_iterations,
        )
        original.add_message("test message", AgentRole.RESEARCHER)

        serialized = original.to_dict()
        restored = TaskState.from_dict(serialized)

        assert restored.query == original.query, "query must survive round-trip"
        assert restored.status == original.status, "status must survive round-trip"
        assert restored.analysis == original.analysis, "analysis must survive round-trip"
        assert restored.research_results == original.research_results, "research_results must survive round-trip"
        assert restored.final_output == original.final_output, "final_output must survive round-trip"
        assert restored.iteration_count == original.iteration_count, "iteration_count must survive round-trip"
        assert restored.max_iterations == original.max_iterations, "max_iterations must survive round-trip"
        assert len(restored.messages) == len(original.messages), "message count must survive round-trip"
        assert restored.messages[0].content == original.messages[0].content, "message content must survive round-trip"
        assert restored.messages[0].sender == original.messages[0].sender, "message sender must survive round-trip"


class TestMessage:
    def test_create(self) -> None:
        msg = Message(content="hello", sender=AgentRole.RESEARCHER)
        assert msg.content == "hello"
        assert msg.timestamp  # Auto-generated


class TestEnums:
    def test_task_status_values(self) -> None:
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETE.value == "complete"

    def test_agent_role_values(self) -> None:
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.REVIEWER.value == "reviewer"
