import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from fastapi.testclient import TestClient

from api import AssistantService, QueryRequest, RateLimiter, app


class FakeAssistant:
    def __init__(self):
        self.calls = 0
        self.llm = object()
        self.reset_calls = 0

    def process_query(self, query, use_rag=True, use_tools=True):
        self.calls += 1
        return {"query": query, "response": f"answer:{query}", "tool_calls": [], "tool_results": {}, "rag_context": ""}

    def add_knowledge(self, documents):
        return None

    def reset_conversation(self):
        self.reset_calls += 1


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("client")
    assert not limiter.allow("client")


def test_service_caches_query_results():
    fake = FakeAssistant()
    service = AssistantService.__new__(AssistantService)
    service.assistant = fake
    service.config = type("Config", (), {"llm": type("LLM", (), {"model": "test", "provider": "test"})()})()
    from api import TTLCache
    service.cache = TTLCache(ttl_seconds=300)
    service.max_retries = 0
    service.retry_delay = 0
    service.fallback = None
    request = QueryRequest(query="hello", use_rag=False, use_tools=False)
    assert service.query(request)["cached"] is False
    assert service.query(request)["cached"] is True
    assert fake.calls == 1


def test_health_endpoint_without_provider_configuration():
    original = __import__("api").service
    __import__("api").service = None
    try:
        response = TestClient(app).get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
    finally:
        __import__("api").service = original
