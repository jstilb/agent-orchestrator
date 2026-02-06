"""State models for multi-agent coordination.

Defines the typed state that flows between agents in the graph.
Uses TypedDict for LangGraph compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    """Status of a task through the agent pipeline."""
    PENDING = "pending"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentRole(str, Enum):
    """Available agent roles in the system."""
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


@dataclass
class Message:
    """A message passed between agents."""
    content: str
    sender: AgentRole
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskState:
    """The shared state that flows through the agent graph.

    This is the core data structure that all agents read and write.
    It tracks the full lifecycle of a task from input to output.
    """
    task_id: str = field(default_factory=lambda: str(uuid4()))
    query: str = ""
    status: TaskStatus = TaskStatus.PENDING
    messages: list[Message] = field(default_factory=list)
    research_results: list[str] = field(default_factory=list)
    analysis: str = ""
    review_notes: list[str] = field(default_factory=list)
    final_output: str = ""
    error: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_message(self, content: str, sender: AgentRole) -> None:
        """Add a message from an agent."""
        self.messages.append(Message(content=content, sender=sender))

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dict for graph compatibility."""
        return {
            "task_id": self.task_id,
            "query": self.query,
            "status": self.status.value,
            "messages": [
                {"content": m.content, "sender": m.sender.value, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "research_results": self.research_results,
            "analysis": self.analysis,
            "review_notes": self.review_notes,
            "final_output": self.final_output,
            "error": self.error,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskState":
        """Deserialize state from dict."""
        state = cls(
            task_id=data.get("task_id", str(uuid4())),
            query=data.get("query", ""),
            status=TaskStatus(data.get("status", "pending")),
            research_results=data.get("research_results", []),
            analysis=data.get("analysis", ""),
            review_notes=data.get("review_notes", []),
            final_output=data.get("final_output", ""),
            error=data.get("error"),
            iteration_count=data.get("iteration_count", 0),
            max_iterations=data.get("max_iterations", 3),
        )
        for msg_data in data.get("messages", []):
            state.messages.append(
                Message(
                    content=msg_data["content"],
                    sender=AgentRole(msg_data["sender"]),
                    timestamp=msg_data.get("timestamp", ""),
                )
            )
        return state
