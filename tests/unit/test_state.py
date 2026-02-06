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
