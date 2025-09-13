import time
import uuid
import httpx


def _client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=60)


def _configure(client: httpx.Client):
    col = f"e2e_{uuid.uuid4().hex[:8]}"
    cfg = {
        "version": "v1.1",
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": "qdrant",
                "port": 6333,
                "collection_name": col,
                "embedding_model_dims": 768,
            },
        },
        "llm": {"provider": "gemini", "config": {"model": "gemini-2.0-flash"}},
        "embedder": {
            "provider": "gemini",
            "config": {"model": "models/text-embedding-004", "embedding_dims": 768},
        },
    }
    # Retry a few times, Qdrant can be slow to accept new collections
    for _ in range(5):
        r = client.post("/configure", json=cfg)
        if r.status_code == 200:
            return r
        time.sleep(2)
    return r


def _create_one(client: httpx.Client, user_id: str):
    payload = {
        "messages": [
            {"role": "user", "content": "Name is Alex. Likes Colombian coffee."},
            {"role": "assistant", "content": "Noted your coffee preference."},
        ],
        "user_id": user_id,
    }
    return client.post("/memories", json=payload)


def _extract_first_id(body):
    try:
        items = body.get("results", body)
        if isinstance(items, dict):
            items = [items]
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                return first.get("id") or first.get("uuid") or first.get("vector_id")
    except Exception:
        pass
    return None


def test_configure_endpoint(base_url):
    client = _client(base_url)
    r = _configure(client)
    assert r.status_code == 200, r.text


def test_create_memories_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    r = _create_one(client, test_ids["user_id"])
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("results", body)
    assert isinstance(items, list) and len(items) >= 1


def test_get_all_memories_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    _create_one(client, test_ids["user_id"])
    r = client.get("/memories", params={"user_id": test_ids["user_id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("results", body)
    assert isinstance(items, list) and len(items) >= 1


def test_get_memory_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    r = _create_one(client, test_ids["user_id"])
    mem_id = _extract_first_id(r.json())
    assert mem_id
    r = client.get(f"/memories/{mem_id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict) and ("memory" in data or "payload" in data)


def test_update_memory_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    r = _create_one(client, test_ids["user_id"])
    mem_id = _extract_first_id(r.json())
    assert mem_id
    r = client.put(f"/memories/{mem_id}", json={"memory": "I prefer espresso now."})
    assert r.status_code == 200, r.text
    assert r.json().get("message")


def test_delete_memory_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    r = _create_one(client, test_ids["user_id"])
    mem_id = _extract_first_id(r.json())
    assert mem_id
    r = client.delete(f"/memories/{mem_id}")
    assert r.status_code == 200, r.text


def test_search_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    _create_one(client, test_ids["user_id"])
    r = client.post("/search", json={"query": "coffee", "user_id": test_ids["user_id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("results", body)
    assert isinstance(items, list)


def test_delete_all_memories_endpoint(base_url, test_ids):
    client = _client(base_url)
    _configure(client)
    _create_one(client, test_ids["user_id"])
    r = client.delete("/memories", params={"user_id": test_ids["user_id"]})
    assert r.status_code in (200, 204, 404), r.text

