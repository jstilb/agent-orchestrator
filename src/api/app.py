"""FastAPI REST API for the agent orchestrator."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.orchestrator import AgentOrchestrator, OrchestratorConfig


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

    return app


app = create_app()
