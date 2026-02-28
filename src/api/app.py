"""FastAPI REST API for the agent orchestrator."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.orchestrator import AgentOrchestrator, OrchestratorConfig
from src.state.models import TaskState, TaskStatus
from src.agents.researcher import ResearchAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.reviewer import ReviewerAgent


class RunRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query for agents to process")
    max_iterations: int = Field(default=3, ge=1, le=10)
    mock: bool = Field(default=True)


class RunResponse(BaseModel):
    task_id: str
    query: str
    status: str
    final_output: str
    message_count: int
    iteration_count: int
    research_count: int


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Orchestrator",
        description="Multi-agent system with state machine coordination",
        version="0.1.0",
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.post("/run", response_model=RunResponse)
    async def run_agents(request: RunRequest) -> RunResponse:
        config = OrchestratorConfig(
            mock=request.mock,
            max_iterations=request.max_iterations,
        )
        orchestrator = AgentOrchestrator(config)
        result = orchestrator.run(request.query)

        return RunResponse(
            task_id=result.task_id,
            query=result.query,
            status=result.status.value,
            final_output=result.final_output,
            message_count=len(result.messages),
            iteration_count=result.iteration_count,
            research_count=len(result.research_results),
        )

    @app.get("/graph")
    async def graph() -> dict[str, list[str]]:
        orchestrator = AgentOrchestrator()
        return orchestrator.get_graph_description()

    @app.websocket("/demo")
    async def demo_websocket(websocket: WebSocket) -> None:
        """WebSocket endpoint that streams TaskState changes in real time.

        Accepts an optional JSON message with {"query": "...", "mock": true}.
        Pushes one JSON frame per TaskStatus transition during pipeline execution.

        Frame format:
            {
                "event": "state_change",
                "status": "researching",
                "task_id": "...",
                "iteration_count": 0,
                "research_count": 0,
                "analysis_length": 0,
                "message_count": 1
            }
        Terminal frame: {"event": "complete", "status": "complete", ...full state dict...}
        """
        await websocket.accept()

        try:
            # Accept optional configuration from client
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                params: dict[str, object] = json.loads(raw)
            except (asyncio.TimeoutError, json.JSONDecodeError):
                params = {}

            query: str = str(params.get("query", "What is the future of AI?"))
            mock: bool = bool(params.get("mock", True))
            max_iterations: int = int(params.get("max_iterations", 3))  # type: ignore[arg-type]

            config = OrchestratorConfig(mock=mock, max_iterations=max_iterations)
            researcher = ResearchAgent(mock=mock)
            analyzer = AnalyzerAgent(mock=mock)
            reviewer = ReviewerAgent(mock=mock, approval_threshold=config.approval_threshold)

            state = TaskState(query=query, max_iterations=max_iterations)

            async def push_state(event: str) -> None:
                frame = {
                    "event": event,
                    "status": state.status.value,
                    "task_id": state.task_id,
                    "iteration_count": state.iteration_count,
                    "research_count": len(state.research_results),
                    "analysis_length": len(state.analysis),
                    "review_notes_count": len(state.review_notes),
                    "message_count": len(state.messages),
                }
                await websocket.send_text(json.dumps(frame))

            # Send initial state
            await push_state("init")

            # Step 1: Research (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            state = await loop.run_in_executor(None, researcher.process, state)
            await push_state("state_change")

            # Step 2-3: Analyze/Review loop
            iteration = 0
            while (
                state.status != TaskStatus.COMPLETE
                and state.status != TaskStatus.FAILED
            ):
                state = await loop.run_in_executor(None, analyzer.process, state)
                await push_state("state_change")

                state = await loop.run_in_executor(None, reviewer.process, state)
                await push_state("state_change")
                iteration += 1

            # Terminal frame includes full state
            terminal_frame = {
                "event": "complete",
                **state.to_dict(),
            }
            await websocket.send_text(json.dumps(terminal_frame))

        except WebSocketDisconnect:
            pass
        except Exception as exc:
            try:
                await websocket.send_text(json.dumps({"event": "error", "message": str(exc)}))
            except Exception:
                pass

    return app


app = create_app()
