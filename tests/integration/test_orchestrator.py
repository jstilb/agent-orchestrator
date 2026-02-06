"""Integration tests for the full orchestrator."""
import pytest
from src.orchestrator import AgentOrchestrator, OrchestratorConfig
from src.state.models import TaskStatus


class TestOrchestrator:
    def test_full_pipeline(self) -> None:
        config = OrchestratorConfig(mock=True, max_iterations=3)
        orchestrator = AgentOrchestrator(config)
        result = orchestrator.run("What is machine learning?")
        assert result.status == TaskStatus.COMPLETE
        assert len(result.final_output) > 0
        assert len(result.research_results) > 0
        assert len(result.messages) > 0

    def test_multiple_queries(self) -> None:
        orchestrator = AgentOrchestrator(OrchestratorConfig(mock=True))
        queries = ["AI safety", "quantum computing", "climate change"]
        for q in queries:
            result = orchestrator.run(q)
            assert result.status == TaskStatus.COMPLETE
            assert result.query == q

    def test_iteration_tracking(self) -> None:
        config = OrchestratorConfig(mock=True, max_iterations=5)
        orchestrator = AgentOrchestrator(config)
        result = orchestrator.run("test query")
        assert result.iteration_count <= config.max_iterations

    def test_graph_description(self) -> None:
        orchestrator = AgentOrchestrator()
        graph = orchestrator.get_graph_description()
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 3

    def test_step_by_step(self) -> None:
        from src.state.models import TaskState
        orchestrator = AgentOrchestrator(OrchestratorConfig(mock=True))
        state = TaskState(query="step test")

        state = orchestrator.run_step(state)
        assert state.status == TaskStatus.RESEARCHING
        assert len(state.research_results) > 0


class TestOrchestratorAPI:
    def test_api_health(self) -> None:
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        client = TestClient(create_app())
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_api_run(self) -> None:
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        client = TestClient(create_app())
        resp = client.post("/run", json={"query": "test query", "mock": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "complete"
        assert len(data["final_output"]) > 0

    def test_api_graph(self) -> None:
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        client = TestClient(create_app())
        resp = client.get("/graph")
        assert resp.status_code == 200
        assert "nodes" in resp.json()
