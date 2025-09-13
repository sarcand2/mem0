import os
import time
import uuid
import pytest
import httpx


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("MEM0_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session", autouse=True)
def wait_for_server(base_url):
    # Wait until the FastAPI server exposes openapi
    deadline = time.time() + 60
    last_err = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/openapi.json", timeout=2)
            if r.status_code == 200:
                return
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(1)
    pytest.skip(f"Server not ready at {base_url}: {last_err}")


@pytest.fixture()
def test_ids():
    # Unique identifiers per test run to avoid cross-test interference
    return {
        "user_id": f"e2e_user_{uuid.uuid4().hex[:8]}",
        "agent_id": f"e2e_agent_{uuid.uuid4().hex[:8]}",
        "run_id": f"e2e_run_{uuid.uuid4().hex[:8]}",
    }


def extract_first_id(payload) -> str | None:
    # Try common shapes: {"results": [{"id": "..."}]} or list of dicts
    try:
        items = payload.get("results", payload)
        if isinstance(items, dict):
            items = [items]
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                return first.get("id") or first.get("uuid") or first.get("vector_id")
    except Exception:
        pass
    return None

