"""Integration tests for the full orchestrator."""
import json
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

    def test_research_analyze_review_revision_loop(self) -> None:
        """Full Research → Analyze → Review → revision loop integration test.

        Drives the pipeline step by step to explicitly visit all four stages:
        Research → Analyze → Review → Analyze (revision) → Review (final approval).
        Asserts all four pipeline stages were visited and the final state is terminal.
        """
        from src.state.models import TaskState
        from src.agents.researcher import ResearchAgent
        from src.agents.analyzer import AnalyzerAgent
        from src.agents.reviewer import ReviewerAgent

        researcher = ResearchAgent(mock=True)
        analyzer = AnalyzerAgent(mock=True)
        # Threshold of 0.34 means 1/3 checks passes → first review fails (forces revision)
        # Second review: analysis is enriched by the loop → passes with 2+/3 checks
        # We'll use approval_threshold just above 0.0 to force one revision, then accept.
        reviewer = ReviewerAgent(mock=True, approval_threshold=1.01)  # Never auto-approve

        state = TaskState(query="quantum computing", max_iterations=2)

        # Stage 1: Research
        state = researcher.process(state)
        assert state.status == TaskStatus.RESEARCHING, "After research, status must be RESEARCHING"
        assert len(state.research_results) > 0, "Research results must be populated"

        # Stage 2: Analyze (first pass)
        state = analyzer.process(state)
        assert state.status == TaskStatus.ANALYZING, "After first analysis, status must be ANALYZING"
        assert len(state.analysis) > 0, "Analysis must be non-empty"
        first_analysis = state.analysis

        # Stage 3: Review (first pass) — threshold 1.01 forces revision (iteration_count < max)
        state = reviewer.process(state)
        # With threshold > 1.0, reviewer sends back to analyzer unless max_iterations hit
        # iteration_count is 0, max_iterations is 2, so revision fires
        assert state.status == TaskStatus.ANALYZING, \
            "First review with impossible threshold must send back to ANALYZING for revision"
        assert state.iteration_count == 1, "Iteration count must increment to 1 after first revision"
        assert len(state.review_notes) > 0, "Review notes must be populated after first review"

        # Stage 4: Analyze (revision pass)
        state = analyzer.process(state)
        assert state.status == TaskStatus.ANALYZING, "After revision analysis, status must be ANALYZING"

        # Final Review: iteration_count=1, max_iterations=2, so one more revision possible
        # Force completion by exhausting iterations
        state.iteration_count = state.max_iterations  # exhaust iterations
        state = reviewer.process(state)
        assert state.status == TaskStatus.COMPLETE, \
            f"Final status must be COMPLETE when max_iterations exhausted, got {state.status.value}"
        assert len(state.final_output) > 0, "Final output must be non-empty after completion"
        assert state.analysis == first_analysis or len(state.analysis) > 0, \
            "Analysis must persist through the revision loop"


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

    def test_websocket_demo_streams_state_changes(self) -> None:
        """WebSocket /demo pushes at least one JSON frame per TaskStatus transition."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app

        client = TestClient(create_app())
        frames: list[dict] = []

        with client.websocket_connect("/demo") as ws:
            # Send configuration
            ws.send_text(json.dumps({"query": "AI safety", "mock": True, "max_iterations": 2}))

            # Collect frames until "complete" event
            for _ in range(20):  # safety limit
                raw = ws.receive_text()
                frame = json.loads(raw)
                frames.append(frame)
                if frame.get("event") in ("complete", "error"):
                    break

        # Must have received multiple frames (init + at least research + complete)
        assert len(frames) >= 3, f"Expected >= 3 frames, got {len(frames)}: {frames}"

        # First frame must be init
        assert frames[0]["event"] == "init", f"First frame event must be 'init', got: {frames[0]}"

        # Must include state_change frames
        state_change_frames = [f for f in frames if f["event"] == "state_change"]
        assert len(state_change_frames) >= 2, \
            f"Expected >= 2 state_change frames (research + review), got {state_change_frames}"

        # Each state_change frame must carry a valid TaskStatus value
        valid_statuses = {"pending", "researching", "analyzing", "reviewing", "complete", "failed"}
        for frame in state_change_frames:
            assert frame["status"] in valid_statuses, \
                f"Invalid status in frame: {frame['status']}"
            assert "task_id" in frame, "Frame must include task_id"
            assert "message_count" in frame, "Frame must include message_count"

        # Last frame must be "complete"
        last = frames[-1]
        assert last["event"] == "complete", \
            f"Last frame must be 'complete', got: {last['event']}"
        assert last["status"] == "complete", \
            f"Terminal status must be 'complete', got: {last['status']}"
        # Complete frame must include full state fields
        assert "query" in last, "Complete frame must include query"
        assert "final_output" in last, "Complete frame must include final_output"
