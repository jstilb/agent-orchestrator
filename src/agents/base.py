"""Base agent with mock/production mode support.

All agents inherit from BaseAgent and implement process().
The base class handles common patterns: logging, error handling,
iteration tracking, and message history.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.state.models import AgentRole, Message, TaskState


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, role: AgentRole, mock: bool = True) -> None:
        self.role = role
        self.mock = mock

    @abstractmethod
    def process(self, state: TaskState) -> TaskState:
        """Process the current state and return updated state."""
        ...

    def _add_message(self, state: TaskState, content: str) -> None:
        """Add a message to state from this agent."""
        state.add_message(content, self.role)
