"""Tests for CLI."""
import json
from unittest.mock import patch
from src.cli import run_demo, run_query, show_graph


class TestCLI:
    def test_demo(self, capsys: object) -> None:
        run_demo()

    def test_query(self, capsys: object) -> None:
        run_query("test question", 2)

    def test_graph(self, capsys: object) -> None:
        show_graph()
