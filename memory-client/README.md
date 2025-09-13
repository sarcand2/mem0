Dagio Memory Client SDK (extracted)

This package provides a lightweight clone of the Mem0 Python client SDK so you can interact with a Mem0-compatible API without depending on the full `mem0ai` package.

Install (editable):

- pip install -e .

Quickstart:

from memory_client import MemoryClient

# Optional token support (not required by server yet)
# export DAGIO_API_KEY=your_token
client = MemoryClient(host="http://localhost:8100")
res = client.add(messages=[{"role":"user","content":"Hello from SDK"}], user_id="sdk-demo")
print(res)

Notes:
- Telemetry is disabled (no-op).
- User setup is stubbed; the client uses an MD5 hash of the API key for a user id, as in mem0 client.
