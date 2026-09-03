"""FastAPI service for the productionized AI assistant."""
import asyncio
import hashlib
import os
import threading
import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from assistant import AIAssistant
from config import get_config


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    use_rag: bool = True
    use_tools: bool = True


class KnowledgeRequest(BaseModel):
    documents: list[str] = Field(min_length=1)


class TTLCache:
    """Small in-memory TTL cache for repeat requests."""

    def __init__(self, ttl_seconds: int = 300, max_items: int = 256):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at <= time.monotonic():
                del self._items[key]
                return None
            return value

    def set(self, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            if len(self._items) >= self.max_items:
                oldest_key = min(self._items, key=lambda item: self._items[item][0])
                del self._items[oldest_key]
            self._items[key] = (time.monotonic() + self.ttl_seconds, value)


class RateLimiter:
    """Fixed-window per-client limiter suitable for a single app instance."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            timestamps = self._requests[client_id]
            while timestamps and timestamps[0] <= now - self.window_seconds:
                timestamps.popleft()
            if len(timestamps) >= self.max_requests:
                return False
            timestamps.append(now)
            return True


class AssistantService:
    """Reliability and performance wrapper around the Task 1 assistant."""

    def __init__(self, config=None, assistant=None):
        self.config = config or get_config()
        self.assistant = assistant or AIAssistant(self.config)
        self.cache = TTLCache(
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            max_items=int(os.getenv("CACHE_MAX_ITEMS", "256")),
        )
        self.rate_limiter = RateLimiter(
            max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "30")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        )
        self.max_retries = int(os.getenv("MAX_RETRIES", "2"))
        self.retry_delay = float(os.getenv("RETRY_DELAY_SECONDS", "0.5"))
        self.fallback = self._build_fallback()

    def _build_fallback(self):
        provider = os.getenv("FALLBACK_PROVIDER", "").strip()
        if not provider or provider.lower() == self.config.llm.provider.lower():
            return None
        try:
            from llm.llm_client import create_llm_client
            return create_llm_client(
                provider=provider,
                api_key=os.getenv("FALLBACK_API_KEY", ""),
                model=os.getenv("FALLBACK_MODEL_NAME", "gpt-4o-mini"),
                temperature=self.config.llm.temperature,
                top_p=self.config.llm.top_p,
                max_tokens=self.config.llm.max_tokens,
            )
        except (ImportError, ValueError):
            return None

    def _cache_key(self, request: QueryRequest) -> str:
        payload = f"{request.query}|{request.use_rag}|{request.use_tools}|{self.config.llm.model}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _run_with_retry(self, request: QueryRequest) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.assistant.process_query(
                    request.query,
                    use_rag=request.use_rag,
                    use_tools=request.use_tools,
                )
            except Exception as error:
                last_error = error
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
        if self.fallback:
            original_llm = self.assistant.llm
            try:
                self.assistant.llm = self.fallback
                return self.assistant.process_query(
                    request.query,
                    use_rag=request.use_rag,
                    use_tools=request.use_tools,
                )
            finally:
                self.assistant.llm = original_llm
        raise last_error or RuntimeError("Assistant request failed")

    def query(self, request: QueryRequest) -> Dict[str, Any]:
        key = self._cache_key(request)
        cached = self.cache.get(key)
        if cached is not None:
            return {**cached, "cached": True}
        result = self._run_with_retry(request)
        self.cache.set(key, result)
        return {**result, "cached": False}


app = FastAPI(title="AI Assistant API", version="2.0.0")
service: Optional[AssistantService] = None
startup_error: Optional[str] = None


@app.on_event("startup")
def initialize_service() -> None:
    global service, startup_error
    try:
        service = AssistantService()
    except Exception as error:
        startup_error = str(error)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok" if service else "degraded", "service_error": startup_error}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


@app.post("/query")
async def query(payload: QueryRequest, request: Request) -> Dict[str, Any]:
    if not service:
        raise HTTPException(status_code=503, detail="Assistant is not configured")
    client_id = request.client.host if request.client else "unknown"
    if not service.rate_limiter.allow(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded; try again later")
    try:
        return await asyncio.to_thread(service.query, payload)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Assistant provider failed: {error}") from error


@app.post("/knowledge")
async def add_knowledge(payload: KnowledgeRequest) -> Dict[str, Any]:
    if not service:
        raise HTTPException(status_code=503, detail="Assistant is not configured")
    try:
        await asyncio.to_thread(service.assistant.add_knowledge, payload.documents)
        return {"status": "ok", "documents_added": len(payload.documents)}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Knowledge ingestion failed: {error}") from error


@app.post("/reset")
def reset() -> Dict[str, str]:
    if not service:
        raise HTTPException(status_code=503, detail="Assistant is not configured")
    service.assistant.reset_conversation()
    return {"status": "ok"}
