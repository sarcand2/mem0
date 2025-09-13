mem0ai (shim)

This is a lightweight shim for the `mem0ai` package that exposes a `mem0` module with:
- `MemoryClient`: backed by `dagio-memory-client` against your orchestrator
- `Memory`: minimal in-process wrapper that calls the orchestrator (no Cloud deps)

Install (editable):
- pip install -e ../memory-client
- pip install -e shim-mem0ai

CrewAI imports `from mem0 import Memory, MemoryClient` and will work with this shim.

