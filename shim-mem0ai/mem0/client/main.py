import os
from typing import Any, Dict, List, Optional

import httpx


class MemoryClient:
    """CrewAI-compatible MemoryClient that calls your Mem0 OSS FastAPI server.

    - Reads base URL from `host` or env `MEM0_API_BASE` (fallback `http://localhost:8000`).
    - Adds optional `Authorization: Token <...>` if `api_key` or env `DAGIO_API_KEY`/`MEM0_API_KEY` is present.
    - Implements the subset CrewAI uses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        org_id: Optional[str] = None,  # compatibility no-op
        project_id: Optional[str] = None,  # compatibility no-op
        client: Optional[httpx.Client] = None,
    ) -> None:
        base = host or os.getenv("MEM0_API_BASE") or "http://localhost:8000"
        token = api_key or os.getenv("DAGIO_API_KEY") or os.getenv("MEM0_API_KEY")
        headers = {"Authorization": f"Token {token}"} if token else {}
        if client is not None:
            self._client = client
            self._client.base_url = httpx.URL(base)
            if headers:
                self._client.headers.update(headers)
        else:
            self._client = httpx.Client(base_url=base, headers=headers, timeout=300)

    def add(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {"messages": messages}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        r = self._client.post("/memories", json=payload)
        r.raise_for_status()
        return r.json()

    def get(self, memory_id: str) -> Dict[str, Any]:
        r = self._client.get(f"/memories/{memory_id}")
        r.raise_for_status()
        return r.json()

    def get_all(self, **kwargs) -> List[Dict[str, Any]]:
        params = {k: v for k, v in kwargs.items() if v is not None}
        r = self._client.get("/memories", params=params)
        r.raise_for_status()
        return r.json()

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        payload = {"query": query}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        r = self._client.post("/search", json=payload)
        r.raise_for_status()
        return r.json()

    def update(self, memory_id: str, text: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if text is None and metadata is None:
            raise ValueError("Either text or metadata must be provided for update.")
        payload: Dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if metadata is not None:
            payload["metadata"] = metadata
        r = self._client.put(f"/memories/{memory_id}", json=payload)
        r.raise_for_status()
        return r.json()

    def delete(self, memory_id: str) -> Dict[str, Any]:
        r = self._client.delete(f"/memories/{memory_id}")
        r.raise_for_status()
        return r.json()

    def delete_all(self, **kwargs) -> Dict[str, Any]:
        params = {k: v for k, v in kwargs.items() if v is not None}
        r = self._client.delete("/memories", params=params)
        r.raise_for_status()
        return r.json()

    def history(self, memory_id: str) -> List[Dict[str, Any]]:
        r = self._client.get(f"/memories/{memory_id}/history")
        r.raise_for_status()
        return r.json()

    def update_project(
        self,
        custom_instructions: Optional[str] = None,
        custom_categories: Optional[List[str]] = None,
        retrieval_criteria: Optional[List[Dict[str, Any]]] = None,
        enable_graph: Optional[bool] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        # No-op for OSS server; return success
        return {
            "status": "ok",
            "custom_instructions": custom_instructions,
            "custom_categories": custom_categories,
            "retrieval_criteria": retrieval_criteria,
            "enable_graph": enable_graph,
            "version": version,
        }
