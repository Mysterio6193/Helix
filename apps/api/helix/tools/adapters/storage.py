"""Storage + memory tool adapters (S3, pgvector)."""
from __future__ import annotations

from typing import Any

from helix.core.storage import S3Storage
from helix.tools.base import Tool, ToolResult


class S3StorageTool(Tool):
    name = "s3_storage"
    description = "Upload bytes / fetch presigned URLs from object storage."

    async def _call(
        self,
        *,
        op: str,
        data: bytes | None = None,
        key: str | None = None,
        prefix: str = "uploads",
        ext: str = "bin",
        content_type: str = "application/octet-stream",
        expires_in: int = 3600,
        **_: Any,
    ) -> ToolResult:
        storage = S3Storage()
        if op == "put":
            if data is None:
                return ToolResult(ok=False, error="data required for put")
            target_key = key or storage.make_key(prefix, ext)
            storage.put_bytes(target_key, data, content_type=content_type)
            return ToolResult(ok=True, data={"s3_key": target_key})
        if op == "presign":
            if not key:
                return ToolResult(ok=False, error="key required for presign")
            url = storage.presigned_get_url(key, expires_in=expires_in)
            return ToolResult(ok=True, data={"url": url, "expires_in": expires_in})
        return ToolResult(ok=False, error=f"unknown op: {op}")


class PgvectorMemoryTool(Tool):
    name = "pgvector_memory"
    description = "Write / search brand memory entries with semantic embeddings."

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        brand_id: Any = None,
        workspace_id: Any = None,
        kind: str = "note",
        content: str = "",
        metadata: dict | None = None,
        query: str = "",
        k: int = 8,
        **_: Any,
    ) -> ToolResult:
        from helix.memory.retriever import topk, write_memory

        if session is None:
            return ToolResult(ok=False, error="session required")
        if op == "write":
            entry = await write_memory(
                session,
                brand_id=brand_id,
                workspace_id=workspace_id,
                kind=kind,
                content=content,
                metadata=metadata or {},
            )
            return ToolResult(ok=True, data={"id": str(entry.id)})
        if op == "search":
            rows = await topk(session, brand_id=brand_id, query=query, k=k)
            return ToolResult(
                ok=True,
                data=[
                    {"id": str(r.id), "kind": r.kind, "content": r.content, "metadata": r.metadata_}
                    for r in rows
                ],
            )
        return ToolResult(ok=False, error=f"unknown op: {op}")
