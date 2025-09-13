import os
from typing import Any, Dict, List, Optional

import httpx


class Memory:
    """Minimal Memory wrapper that uses the orchestrator REST API.

    Provides the subset CrewAI uses when no api_key is set (OSS path):
    - from_config
    - add, search, reset
    """

    def __init__(self, host: Optional[str] = None, token: Optional[str] = None) -> None:
        self._host = host or os.getenv("MEM0_API_BASE") or os.getenv("DAGIO_API_BASE") or "http://localhost:8100"
        self._token = token or os.getenv("DAGIO_API_KEY") or os.getenv("MEM0_API_KEY")
        headers = {"Authorization": f"Token {self._token}"} if self._token else {}
        self._client = httpx.Client(base_url=self._host, headers=headers, timeout=300)

    @classmethod
    def from_config(cls, config: Dict[str, Any]):
        # Optionally read a host override from config
        host = (
            (config or {}).get("host")
            or os.getenv("MEM0_API_BASE")
            or os.getenv("DAGIO_API_BASE")
            or "http://localhost:8100"
        )
        token = os.getenv("DAGIO_API_KEY") or os.getenv("MEM0_API_KEY")
        return cls(host=host, token=token)

    # Mirror the signature used by CrewAI's Mem0Storage
    def add(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {"messages": messages}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        r = self._client.post("/memories/", json=payload)
        r.raise_for_status()
        return r.json()

    def search(self, **kwargs) -> Dict[str, Any]:
        r = self._client.post("/search", json=kwargs)
        r.raise_for_status()
        return r.json()

    def reset(self) -> Dict[str, Any]:
        # Call the server reset endpoint if available; fallback to deleting all
        try:
            r = self._client.post("/reset")
            r.raise_for_status()
            return r.json()
        except Exception:
            r = self._client.delete("/memories/")
            r.raise_for_status()
            return r.json()
