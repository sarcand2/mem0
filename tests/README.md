# Test Suite Guide

This repository contains a focused test suite for the `mem0` library under `tests/`, alongside other projects in this monorepo. To avoid collecting tests from sibling projects (e.g., `embedchain`), always invoke pytest by targeting the `tests/` directory explicitly.

## Structure
- `tests/llms`: unit tests for LLM providers (e.g., Gemini, OpenAI) — mostly mocked.
- `tests/embeddings`: unit tests for embedding providers — mostly mocked.
- `tests/vector_stores`: unit tests for vector-store integrations (Qdrant, PGVector, etc.) — rely on mocks and do not require live services.
- `tests/memory`: tests of memory orchestration and graph store adapters (mocked).
- Top-level tests: lightweight integration and configuration validation.

## Prerequisites
- Python 3.9–3.12 recommended (3.13 may work but is less exercised).
- Install `mem0` in editable mode, with the minimum packages to run the suite:

```bash
python -m pip install -U pip
python -m pip install -e .[test]
# Optional (recommended for provider coverage used by tests):
python -m pip install google-genai qdrant-client
```

If you want fuller coverage for providers used in tests (OpenAI, Azure, Redis, Elasticsearch, etc.), install extra feature sets. Note some packages may require system deps (e.g., FAISS) and are best installed in Linux containers:

```bash
# Attempt full extras locally (may fail for some binaries on Windows/macOS)
python -m pip install -e .[test,vector_stores,llms,extras]
```

## Running Tests

Run only the `mem0` tests (recommended):

```bash
pytest -q tests
```

Run a quick smoke subset (no external services required):

```bash
pytest -q tests/llms/test_gemini.py tests/vector_stores/test_qdrant.py
```

Filter by keyword (include/exclude):

```bash
# Run only qdrant-related tests
pytest -q tests -k qdrant

# Exclude cloud-provider heavy tests
pytest -q tests -k "not (azure or vertex or databricks or supabase)"

## End-to-End (E2E) against localhost

The `tests/e2e` folder contains E2E tests that exercise the running FastAPI server via HTTP.

Prerequisites:
- Start the stack first: `cd server && docker compose up -d --build`.
- Ensure `server/.env` has a valid `GOOGLE_API_KEY` and that Qdrant/Memgraph are healthy.

Run E2E tests:

```
pytest -q tests/e2e
```

Optional:

```
# Point to a non-default base URL
MEM0_BASE_URL=http://127.0.0.1:8000 pytest -q tests/e2e
```
```

## Running inside Docker (Linux)

The dev container under `server/docker-compose.yaml` already installs `mem0` with extras. To run tests there:

```bash
cd server
docker compose up -d --build
docker compose exec mem0 bash -lc "pip install pytest && pytest -q /app/packages/mem0/tests"
```

Notes:
- Some providers require credentials to execute real network calls. The tests here are generally mocked; no keys are required. If you opt-in to real calls, export env vars (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`).
- If you see collection errors from unrelated projects (e.g., `embedchain`), ensure you are running `pytest tests` (path-scoped), not `pytest` from repo root.

## Troubleshooting
- Import errors for provider SDKs: install the specific SDK or install extras as shown above.
- Binary/install failures on Windows/macOS: prefer running in the Docker dev container (Linux) and executing pytest there.
- Long/complex external tests: use `-k` to narrow scope or mark slow tests via `-m` if markers are added in future.
