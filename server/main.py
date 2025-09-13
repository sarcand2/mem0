import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from mem0 import Memory

# Runtime patch to avoid modifying the mem0 open-source package on disk.
# Replaces Memgraph node-similarity with vector index search for query embeddings.
try:
    from mem0.memory.memgraph_memory import MemoryGraph  # type: ignore

    def _patched_search_graph_db(self, node_list, filters, limit=100):
        """Vector-index based neighborhood search using MAGE vector_search.

        Avoids calling node_similarity.cosine_pairwise with invalid arg types.
        """
        result_relations = []
        for node in node_list:
            n_embedding = self.embedding_model.embed(node)
            k = min(max(1, int(limit or 10)), 1000)

            if filters.get("agent_id"):
                cypher_query = """
                CALL vector_search.search("memzero", $k, $n_embedding)
                YIELD node, similarity
                WITH node, similarity
                WHERE node.user_id = $user_id AND node.agent_id = $agent_id AND similarity >= $threshold
                MATCH (node)-[r]->(m:Entity {user_id: $user_id, agent_id: $agent_id})
                RETURN node.name AS source, id(node) AS source_id, type(r) AS relationship, id(r) AS relation_id, m.name AS destination, id(m) AS destination_id, similarity
                UNION
                CALL vector_search.search("memzero", $k, $n_embedding)
                YIELD node, similarity
                WITH node, similarity
                WHERE node.user_id = $user_id AND node.agent_id = $agent_id AND similarity >= $threshold
                MATCH (m:Entity {user_id: $user_id, agent_id: $agent_id})-[r]->(node)
                RETURN m.name AS source, id(m) AS source_id, type(r) AS relationship, id(r) AS relation_id, node.name AS destination, id(node) AS destination_id, similarity
                ORDER BY similarity DESC
                LIMIT $limit;
                """
                params = {
                    "n_embedding": n_embedding,
                    "threshold": getattr(self, "threshold", 0.7),
                    "user_id": filters["user_id"],
                    "agent_id": filters["agent_id"],
                    "limit": limit,
                    "k": k,
                }
            else:
                cypher_query = """
                CALL vector_search.search("memzero", $k, $n_embedding)
                YIELD node, similarity
                WITH node, similarity
                WHERE node.user_id = $user_id AND similarity >= $threshold
                MATCH (node)-[r]->(m:Entity {user_id: $user_id})
                RETURN node.name AS source, id(node) AS source_id, type(r) AS relationship, id(r) AS relation_id, m.name AS destination, id(m) AS destination_id, similarity
                UNION
                CALL vector_search.search("memzero", $k, $n_embedding)
                YIELD node, similarity
                WITH node, similarity
                WHERE node.user_id = $user_id AND similarity >= $threshold
                MATCH (m:Entity {user_id: $user_id})-[r]->(node)
                RETURN m.name AS source, id(m) AS source_id, type(r) AS relationship, id(r) AS relation_id, node.name AS destination, id(node) AS destination_id, similarity
                ORDER BY similarity DESC
                LIMIT $limit;
                """
                params = {
                    "n_embedding": n_embedding,
                    "threshold": getattr(self, "threshold", 0.7),
                    "user_id": filters["user_id"],
                    "limit": limit,
                    "k": k,
                }

            ans = self.graph.query(cypher_query, params=params)
            result_relations.extend(ans)

        return result_relations

    # Apply patch once at import time
    MemoryGraph._search_graph_db = _patched_search_graph_db  # type: ignore
except Exception as _e:
    logging.warning(f"Skipping Memgraph search patch: {_e}")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()


QDRANT_HOST = os.environ.get("MEMORY_QDRANT_HOST", "qdrant")
QDRANT_PORT = os.environ.get("MEMORY_QDRANT_PORT", "6333")
QDRANT_COLLECTION_NAME = os.environ.get(
    "MEMORY_QDRANT_COLLECTION_NAME", "memories")

MEMGRAPH_URI = os.environ.get("MEMORY_MEMGRAPH_URI", "bolt://memgraph:7687")
# Provide non-empty defaults to satisfy config validation
MEMGRAPH_USERNAME = os.environ.get(
    "MEMORY_MEMGRAPH_USERNAME", "memory_graph_user")
MEMGRAPH_PASSWORD = os.environ.get(
    "MEMORY_MEMGRAPH_PASSWORD", "mem0ry_graph_P@ss")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
HISTORY_DB_PATH = os.environ.get(
    "MEMORY_HISTORY_DB_PATH", "/app/history/history.db")

DEFAULT_CONFIG = {
    "version": "v1.1",
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": QDRANT_HOST,
            "port": int(QDRANT_PORT),
            "collection_name": QDRANT_COLLECTION_NAME,
            "embedding_model_dims": 768,
        },
    },
    "graph_store": {
        "provider": "memgraph",
        "config": {"url": MEMGRAPH_URI, "username": MEMGRAPH_USERNAME, "password": MEMGRAPH_PASSWORD},
    },
    "llm": {
        "provider": "gemini",
        "config": {"api_key": GOOGLE_API_KEY, "temperature": 0.2, "model": "gemini-2.0-flash"},
    },
    "embedder": {
        "provider": "gemini",
        "config": {
            "api_key": GOOGLE_API_KEY,
            "model": "models/text-embedding-004",
            "embedding_dims": 768,
            "output_dimensionality": 768,
        },
    },
    "history_db_path": HISTORY_DB_PATH,
}


MEMORY_INSTANCE = Memory.from_config(DEFAULT_CONFIG)

app = FastAPI(
    title="Mem0 REST APIs",
    description="A REST API for managing and searching memories for your AI Agents and Apps.",
    version="1.0.0",
)


class Message(BaseModel):
    role: str = Field(...,
                      description="Role of the message (user or assistant).")
    content: str = Field(..., description="Message content.")


class MemoryCreate(BaseModel):
    messages: List[Message] = Field(...,
                                    description="List of messages to store.")
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query.")
    user_id: Optional[str] = None
    run_id: Optional[str] = None
    agent_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


@app.post("/configure", summary="Configure Mem0")
def set_config(config: Dict[str, Any]):
    """Set memory configuration.

    Adjusts incoming hosts to match container service names when applicable.
    """
    try:
        cfg = dict(config)
        # Normalize vector store host for Docker service name
        try:
            vs = cfg.get("vector_store", {})
            if vs.get("provider") == "qdrant":
                vsc = vs.get("config", {})
                host = vsc.get("host")
                if host in ("qdrant", "localhost"):
                    vsc["host"] = os.getenv("MEMORY_QDRANT_HOST", host)
                vs["config"] = vsc
                cfg["vector_store"] = vs
        except Exception:
            pass

        # Normalize memgraph URI if present
        try:
            gs = cfg.get("graph_store", {})
            if gs.get("provider") == "memgraph":
                gsc = gs.get("config", {})
                url = gsc.get("url")
                default_uri = os.getenv("MEMORY_MEMGRAPH_URI")
                if default_uri and url:
                    # If url points to 'memgraph' service, replace with env URI
                    if "memgraph" in url and "memory-memgraph" not in url:
                        gsc["url"] = default_uri
                elif default_uri and not url:
                    gsc["url"] = default_uri
                gs["config"] = gsc
                cfg["graph_store"] = gs
        except Exception:
            pass

        # Ensure GOOGLE_API_KEY is available for gemini providers
        if not os.getenv("GOOGLE_API_KEY"):
            logging.warning("GOOGLE_API_KEY not set; Gemini LLM/embedder may fail")

        global MEMORY_INSTANCE
        MEMORY_INSTANCE = Memory.from_config(cfg)
        return {"message": "Configuration set successfully"}
    except Exception as e:
        logging.exception("Error in configure:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories", summary="Create memories")
def add_memory(memory_create: MemoryCreate):
    """Store new memories."""
    if not any([memory_create.user_id, memory_create.agent_id, memory_create.run_id]):
        raise HTTPException(
            status_code=400, detail="At least one identifier (user_id, agent_id, run_id) is required.")

    params = {k: v for k, v in memory_create.model_dump(
    ).items() if v is not None and k != "messages"}
    try:
        response = MEMORY_INSTANCE.add(
            messages=[m.model_dump() for m in memory_create.messages], **params)
        return JSONResponse(content=response)
    except Exception as e:
        # This will log the full traceback
        logging.exception("Error in add_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories", summary="Get memories")
def get_all_memories(
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """Retrieve stored memories."""
    if not any([user_id, run_id, agent_id]):
        raise HTTPException(
            status_code=400, detail="At least one identifier is required.")
    try:
        params = {
            k: v for k, v in {"user_id": user_id, "run_id": run_id, "agent_id": agent_id}.items() if v is not None
        }
        return MEMORY_INSTANCE.get_all(**params)
    except Exception as e:
        logging.exception("Error in get_all_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}", summary="Get a memory")
def get_memory(memory_id: str):
    """Retrieve a specific memory by ID."""
    try:
        return MEMORY_INSTANCE.get(memory_id)
    except Exception as e:
        logging.exception("Error in get_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", summary="Search memories")
def search_memories(search_req: SearchRequest):
    """Search for memories based on a query."""
    try:
        params = {k: v for k, v in search_req.model_dump(
        ).items() if v is not None and k != "query"}
        return MEMORY_INSTANCE.search(query=search_req.query, **params)
    except Exception as e:
        logging.exception("Error in search_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/memories/{memory_id}", summary="Update a memory")
def update_memory(memory_id: str, updated_memory: Dict[str, Any]):
    """Update an existing memory with new content.

    Args:
        memory_id (str): ID of the memory to update
        updated_memory (str): New content to update the memory with

    Returns:
        dict: Success message indicating the memory was updated
    """
    try:
        # Accept either a raw string under 'memory'/'text' key or a full dict.
        data = updated_memory
        if isinstance(updated_memory, dict):
            if "memory" in updated_memory:
                data = updated_memory["memory"]
            elif "text" in updated_memory:
                data = updated_memory["text"]
        if not isinstance(data, str):
            raise HTTPException(
                status_code=400, detail="Body must include 'memory' or 'text' as string.")
        return MEMORY_INSTANCE.update(memory_id=memory_id, data=data)
    except Exception as e:
        logging.exception("Error in update_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}/history", summary="Get memory history")
def memory_history(memory_id: str):
    """Retrieve memory history."""
    try:
        return MEMORY_INSTANCE.history(memory_id=memory_id)
    except Exception as e:
        logging.exception("Error in memory_history:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories/{memory_id}", summary="Delete a memory")
def delete_memory(memory_id: str):
    """Delete a specific memory by ID."""
    try:
        MEMORY_INSTANCE.delete(memory_id=memory_id)
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        logging.exception("Error in delete_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories", summary="Delete all memories")
def delete_all_memories(
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """Delete all memories for a given identifier."""
    if not any([user_id, run_id, agent_id]):
        raise HTTPException(
            status_code=400, detail="At least one identifier is required.")
    try:
        params = {
            k: v for k, v in {"user_id": user_id, "run_id": run_id, "agent_id": agent_id}.items() if v is not None
        }
        MEMORY_INSTANCE.delete_all(**params)
        return {"message": "All relevant memories deleted"}
    except Exception as e:
        logging.exception("Error in delete_all_memories:")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset", summary="Reset all memories")
def reset_memory():
    """Completely reset stored memories."""
    try:
        MEMORY_INSTANCE.reset()
        return {"message": "All memories reset"}
    except Exception as e:
        logging.exception("Error in reset_memory:")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", summary="Redirect to the OpenAPI documentation", include_in_schema=False)
def home():
    """Redirect to the OpenAPI documentation."""
    return RedirectResponse(url="/docs")
