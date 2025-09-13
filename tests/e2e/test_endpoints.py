import httpx
import pytest


def extract_first_id(payload) -> str | None:
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


def test_e2e_memories_crud_flow(base_url, test_ids):
    client = httpx.Client(base_url=base_url, timeout=60)

    # Reconfigure to an isolated Qdrant collection to avoid dim mismatch
    import uuid as _uuid
    col = f"e2e_{_uuid.uuid4().hex[:8]}"
    cfg = {
        "version": "v1.1",
        "vector_store": {
            "provider": "qdrant",
            "config": {"host": "qdrant", "port": 6333, "collection_name": col, "embedding_model_dims": 768},
        },
        "llm": {"provider": "gemini", "config": {"model": "gemini-2.0-flash"}},
        "embedder": {"provider": "gemini", "config": {"model": "models/text-embedding-004", "embedding_dims": 768}},
    }
    # Retry configure a few times in case Qdrant is still warming up
    for _ in range(5):
        rc = client.post("/configure", json=cfg)
        if rc.status_code == 200:
            break
        import time as _t
        _t.sleep(2)
    assert rc.status_code == 200, rc.text

    # 1) Create memories
    payload = {
        "messages": [
            {"role": "user", "content": "Hi, I'm Alex. I like Colombian coffee."},
            {"role": "assistant", "content": "Noted: you like Colombian coffee."},
        ],
        "user_id": test_ids["user_id"],
        # agent_id/run_id optional here
    }
    r = client.post("/memories", json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    memory_id = extract_first_id(created)

    # 2) Get all for user
    r = client.get("/memories", params={"user_id": test_ids["user_id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    all_items = body.get("results", body)
    assert isinstance(all_items, list) and len(all_items) >= 1

    # 3) Search
    r = client.post(
        "/search",
        json={"query": "coffee", "user_id": test_ids["user_id"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    search_results = body.get("results", body)
    assert isinstance(search_results, list)

    # 4) Get one + history (if we have an id)
    if memory_id:
        r = client.get(f"/memories/{memory_id}")
        assert r.status_code == 200, r.text

        r = client.get(f"/memories/{memory_id}/history")
        assert r.status_code == 200, r.text

        # 5) Update one
        update_payload = {"memory": "I prefer espresso now."}
        r = client.put(f"/memories/{memory_id}", json=update_payload)
        assert r.status_code == 200, r.text

        # 6) Delete one
        r = client.delete(f"/memories/{memory_id}")
        assert r.status_code == 200, r.text

    # 7) Cleanup: delete all for user
    r = client.delete("/memories", params={"user_id": test_ids["user_id"]})
    # Endpoint returns 200 on success; tolerate 404/204 if already gone
    assert r.status_code in (200, 204, 404)


def test_e2e_configure_endpoint(base_url):
    # Push a no-op config aligned with defaults so running stack remains valid
    cfg = {
        "version": "v1.1",
        "vector_store": {
            "provider": "qdrant",
            "config": {"host": "qdrant", "port": 6333, "collection_name": "memories", "embedding_model_dims": 768},
        },
        "graph_store": {
            "provider": "memgraph",
            "config": {"url": "bolt://memgraph:7687", "username": "memgraph", "password": "mem0graph"},
        },
        "llm": {"provider": "gemini", "config": {"model": "gemini-2.0-flash"}},
        "embedder": {"provider": "gemini", "config": {"model": "models/text-embedding-004", "embedding_dims": 768}},
    }

    r = httpx.post(f"{base_url}/configure", json=cfg, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict) and "message" in body
