import os
import logging
import warnings
from typing import Any, Dict, List, Optional

import httpx

from memory_client.utils import api_error_handler
from memory_client.setup import setup_config
from memory_client.telemetry import capture_client_event

logger = logging.getLogger(__name__)

warnings.filterwarnings("default", category=DeprecationWarning)

# Initialize any local config (no-op stub)
setup_config()


class MemoryClient:
    """Lightweight client for the Mem0-compatible orchestrator (no auth).

    Exposes CRUD/search endpoints under `/memories` without authentication.
    """

    def __init__(self, host: Optional[str] = None, token: Optional[str] = None, client: Optional[httpx.Client] = None):
        self.host = host or "http://localhost:8100"
        self.token = token or os.getenv("DAGIO_API_KEY") or os.getenv("MEM0_API_KEY")
        default_headers = {"Authorization": f"Token {self.token}"} if self.token else None
        if client is not None:
            self.client = client
            self.client.base_url = httpx.URL(self.host)
            if default_headers:
                self.client.headers.update(default_headers)
        else:
            self.client = httpx.Client(base_url=self.host, timeout=300, headers=default_headers or {})
        capture_client_event("client.init", self, {"sync_type": "sync"})

    @api_error_handler
    def add(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {"messages": messages}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        response = self.client.post("/memories/", json=payload)
        response.raise_for_status()
        capture_client_event("client.add", self, {"keys": list(kwargs.keys()), "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def get(self, memory_id: str) -> Dict[str, Any]:
        response = self.client.get(f"/memories/{memory_id}/")
        response.raise_for_status()
        capture_client_event("client.get", self, {"memory_id": memory_id, "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def get_all(self, **kwargs) -> List[Dict[str, Any]]:
        params = {k: v for k, v in (kwargs or {}).items() if v is not None}
        response = self.client.get("/memories/", params=params)
        response.raise_for_status()
        capture_client_event("client.get_all", self, {"keys": list(params.keys()), "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        payload = {"query": query}
        payload.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        response = self.client.post("/memories/search/", json=payload)
        response.raise_for_status()
        capture_client_event("client.search", self, {"keys": list((kwargs or {}).keys()), "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def update(self, memory_id: str, text: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if text is None and metadata is None:
            raise ValueError("Either text or metadata must be provided for update.")
        payload: Dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if metadata is not None:
            payload["metadata"] = metadata
        response = self.client.put(f"/memories/{memory_id}/", json=payload)
        response.raise_for_status()
        capture_client_event("client.update", self, {"memory_id": memory_id, "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def delete(self, memory_id: str) -> Dict[str, Any]:
        response = self.client.delete(f"/memories/{memory_id}/")
        response.raise_for_status()
        capture_client_event("client.delete", self, {"memory_id": memory_id, "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def delete_all(self, **kwargs) -> Dict[str, Any]:
        params = {k: v for k, v in (kwargs or {}).items() if v is not None}
        response = self.client.delete("/memories/", params=params)
        response.raise_for_status()
        capture_client_event("client.delete_all", self, {"keys": list(params.keys()), "sync_type": "sync"})
        return response.json()

    @api_error_handler
    def history(self, memory_id: str) -> List[Dict[str, Any]]:
        response = self.client.get(f"/memories/{memory_id}/history/")
        response.raise_for_status()
        capture_client_event("client.history", self, {"memory_id": memory_id, "sync_type": "sync"})
        return response.json()


class AsyncMemoryClient:
    """Async client for the Mem0-compatible orchestrator (no auth)."""

    def __init__(self, host: Optional[str] = None, token: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.host = host or "http://localhost:8100"
        self.token = token or os.getenv("DAGIO_API_KEY") or os.getenv("MEM0_API_KEY")
        default_headers = {"Authorization": f"Token {self.token}"} if self.token else None
        if client is not None:
            self.async_client = client
            self.async_client.base_url = httpx.URL(self.host)
            if default_headers:
                self.async_client.headers.update(default_headers)
        else:
            self.async_client = httpx.AsyncClient(base_url=self.host, timeout=300, headers=default_headers or {})
        capture_client_event("client.init", self, {"sync_type": "async"})

    @api_error_handler
    async def add(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {"messages": messages}
        payload.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        response = await self.async_client.post("/memories/", json=payload)
        response.raise_for_status()
        capture_client_event("client.add", self, {"keys": list((kwargs or {}).keys()), "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def get(self, memory_id: str) -> Dict[str, Any]:
        response = await self.async_client.get(f"/memories/{memory_id}/")
        response.raise_for_status()
        capture_client_event("client.get", self, {"memory_id": memory_id, "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def get_all(self, **kwargs) -> List[Dict[str, Any]]:
        params = {k: v for k, v in (kwargs or {}).items() if v is not None}
        response = await self.async_client.get("/memories/", params=params)
        response.raise_for_status()
        capture_client_event("client.get_all", self, {"keys": list(params.keys()), "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        payload = {"query": query}
        payload.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        response = await self.async_client.post("/memories/search/", json=payload)
        response.raise_for_status()
        capture_client_event("client.search", self, {"keys": list((kwargs or {}).keys()), "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def update(self, memory_id: str, text: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if text is None and metadata is None:
            raise ValueError("Either text or metadata must be provided for update.")
        payload: Dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if metadata is not None:
            payload["metadata"] = metadata
        response = await self.async_client.put(f"/memories/{memory_id}/", json=payload)
        response.raise_for_status()
        capture_client_event("client.update", self, {"memory_id": memory_id, "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def delete(self, memory_id: str) -> Dict[str, Any]:
        response = await self.async_client.delete(f"/memories/{memory_id}/")
        response.raise_for_status()
        capture_client_event("client.delete", self, {"memory_id": memory_id, "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def delete_all(self, **kwargs) -> Dict[str, Any]:
        params = {k: v for k, v in (kwargs or {}).items() if v is not None}
        response = await self.async_client.delete("/memories/", params=params)
        response.raise_for_status()
        capture_client_event("client.delete_all", self, {"keys": list(params.keys()), "sync_type": "async"})
        return response.json()

    @api_error_handler
    async def history(self, memory_id: str) -> List[Dict[str, Any]]:
        response = await self.async_client.get(f"/memories/{memory_id}/history/")
        response.raise_for_status()
        capture_client_event("client.history", self, {"memory_id": memory_id, "sync_type": "async"})
        return response.json()
















