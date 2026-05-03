# Basic Tests for Our Newsletter Pipeline.

import sys
import os
from unittest.mock import patch
# Import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from myapi.langgraph.nodes import (
    scoring_node,
    crawl_node,
    newsletter_generator_node,
    reflection_node,
    should_continue,
    search_node
)
from myapi.langgraph.graph import create_newsletter_agent


# Mocks - this means faking LLM response to test our Pipeline 

class MockScoreLLM:
    def invoke(self, prompt):
        class Res:
            content = """[
                {"id": 0, "score": 9, "reason": "important"},
                {"id": 1, "score": 7, "reason": "relevant"}
            ]"""
        return Res()


class MockGenLLM:
    def invoke(self, prompt):
        class Res:
            content = "<ul><li>Test News</li></ul>"
        return Res()


class MockReflectLLM:
    def invoke(self, prompt):
        class Res:
            content = '{"status": "publish"}'
        return Res()


# Tests - test if every node is working properly with mock LLM data

def test_scoring_node_success():
    state = {
        "search_results": [
            {"title": "News 1", "url": "url1", "content": "text"},
            {"title": "News 2", "url": "url2", "content": "text"}
        ]
    }

    result = scoring_node(state, llm=MockScoreLLM())

    assert "top_links" in result
    assert len(result["top_links"]) == 2
    assert result["top_links"][0]["score"] == 9


@patch("myapi.langgraph.nodes.trafilatura.fetch_url")
@patch("myapi.langgraph.nodes.trafilatura.extract")
def test_crawl_node(mock_extract, mock_fetch):
    mock_fetch.return_value = "<html>content</html>"
    mock_extract.return_value = "clean extracted text"

    state = {"top_links": [{"url": "http://test.com"}]}

    result = crawl_node(state)

    assert "raw_markdown" in result
    assert len(result["raw_markdown"]) == 1
    assert "clean extracted text" in result["raw_markdown"][0]


def test_newsletter_generator(tmp_path, monkeypatch):
    template = tmp_path / "newsletter_template.html"
    template.write_text("{{ newsletter_content }}")

    import builtins

    real_open = builtins.open

    monkeypatch.setattr(
        builtins,
        "open",
        lambda *a, **k: real_open(template)
    )
    state = {
        "raw_markdown": ["news content"],
        "critique": [],
        "iteration_count": 0
    }

    result = newsletter_generator_node(state, llm=MockGenLLM())

    assert "newsletter" in result
    assert "<ul>" in result["newsletter"]
    assert result["iteration_count"] == 1


def test_reflection_publish():
    state = {
        "iteration_count": 1,
        "raw_markdown": ["data"],
        "newsletter": "content"
    }

    result = reflection_node(state, llm=MockReflectLLM())

    assert result["status"] == "publish"


def test_should_continue_publish():
    assert should_continue({"status": "publish", "iteration_count": 1}) == "end"


def test_should_continue_revise():
    assert should_continue({"status": "revise", "iteration_count": 1}) == "revise"


def test_should_continue_max_iter():
    assert should_continue({"status": "revise", "iteration_count": 2}) == "end"


@patch("myapi.langgraph.nodes.WebSearch.search_the_web")
def test_search_node(mock_search):
    mock_search.return_value = [{"title": "test"}]

    result = search_node({"query": "news"})

    assert "search_results" in result
    assert len(result["search_results"]) == 1


def test_graph_creation():
    agent = create_newsletter_agent(score_llm=None, flash_llm=None)
    assert agent is not None