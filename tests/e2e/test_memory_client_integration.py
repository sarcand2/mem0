import os
import socket
import time

import pytest


def _is_host_up(host: str) -> bool:
    try:
        from urllib.parse import urlparse
        import httpx

        parsed = urlparse(host)
        scheme = parsed.scheme or "http"
        netloc = parsed.netloc or parsed.path
        if ":" in netloc:
            hostname, port = netloc.split(":", 1)
            port = int(port)
        else:
            hostname = netloc
            port = 443 if scheme == "https" else 80
        with socket.create_connection((hostname, port), timeout=2):
            pass
        with httpx.Client(base_url=f"{scheme}://{hostname}:{port}", timeout=2) as c:
            r = c.get("/")
            return r.status_code < 500
    except Exception:
        return False


@pytest.mark.integration
def test_memory_client_orchestrator_e2e():
    # Run only when an orchestrator host is explicitly provided
    host = os.getenv("ORCH_HOST")
    if not host:
        pytest.skip("Set ORCH_HOST to run orchestrator E2E test")
    if not _is_host_up(host):
        pytest.skip(f"Orchestrator not reachable: {host}")

    try:
        from memory_client import MemoryClient
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).resolve().parents[2] / "memory-client"))
        from memory_client import MemoryClient

    client = MemoryClient(host=host)

    # Create memory
    payload = {
        "messages": [{"role": "user", "content": "E2E test memory"}],
        "user_id": "e2e-sdk",
    }
    res = client.add(**payload)
    assert isinstance(res, dict)

    # Fetch all
    lst = client.get_all(user_id="e2e-sdk")
    assert isinstance(lst, (list, dict))  # server may return list or dict depending on implementation

    # Search
    search = client.search(query="E2E", user_id="e2e-sdk")
    assert search is not None
