"""MCP (Model Context Protocol) server implementation.

Exposes Helix tools via MCP protocol for integration with Claude Desktop,
IDEs, and other MCP clients.

Supports two transports:
- SSE: Server-Sent Events over HTTP
- Stdio: Standard input/output for local execution

All tool calls resolve credentials via the integration resolver.
Nothing is hardcoded or mocked.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from helix.core.logging import get_logger
from helix.integrations.resolver import get_integration_credentials
from helix.tools.base import Tool, ToolResult
from helix.tools.registry import list_tools

log = get_logger("helix.mcp")


class McpError(Exception):
    """MCP protocol error."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


# MCP error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _make_response(id: Any, result: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 response."""
    resp: dict[str, Any] = {"jsonrpc": "2.0", "id": id}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result or {}
    return resp


def _make_error(id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return _make_response(id, error=err)


class McpServer:
    """MCP server that exposes Helix tools."""

    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())
        self._tools: dict[str, Tool] = {}
        self._init = False

    async def initialize(self) -> None:
        """Load all registered tools."""
        if self._init:
            return
        for tool in list_tools():
            self._tools[tool.name] = tool
        self._init = True
        log.info("mcp_server_initialized", tool_count=len(self._tools))

    def _list_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for MCP protocol."""
        return [
            {
                "name": name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "description": "Operation to perform"},
                        "session": {"type": "string", "description": "Session identifier"},
                        "workspace_id": {"type": "string", "description": "Workspace UUID"},
                    },
                    "required": ["op"],
                },
            }
            for name, tool in self._tools.items()
        ]

    async def _call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        db_session: Any = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a tool and return MCP-formatted content."""
        tool = self._tools.get(name)
        if not tool:
            raise McpError(METHOD_NOT_FOUND, f"Tool not found: {name}")

        # Extract workspace_id from arguments if provided
        ws_id = arguments.pop("workspace_id", workspace_id)
        session = arguments.pop("session", db_session)

        # Remove internal fields that tools shouldn't receive directly
        arguments.pop("_meta", None)

        try:
            result: ToolResult = await tool(
                session=session,
                workspace_id=ws_id,
                **arguments,
            )
        except Exception as exc:
            log.exception("mcp_tool_call_failed", tool=name)
            raise McpError(INTERNAL_ERROR, f"Tool execution failed: {exc}") from exc

        if result.ok:
            content = json.dumps(result.data, indent=2) if result.data else "Success"
            return [{"type": "text", "text": content}]
        else:
            return [{"type": "text", "text": f"Error: {result.error}"}]

    async def handle_request(
        self,
        request: dict[str, Any],
        db_session: Any = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle a single MCP JSON-RPC request."""
        await self.initialize()

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if not method:
            return _make_error(req_id, INVALID_REQUEST, "Method required")

        try:
            if method == "initialize":
                return _make_response(
                    req_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {},
                        },
                        "serverInfo": {
                            "name": "helix-mcp",
                            "version": "1.0.0",
                        },
                    },
                )

            elif method == "initialized":
                return _make_response(req_id)

            elif method == "tools/list":
                return _make_response(req_id, {"tools": self._list_tools()})

            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                content = await self._call_tool(name, arguments, db_session, workspace_id)
                return _make_response(req_id, {"content": content})

            elif method == "resources/list":
                return _make_response(req_id, {"resources": []})

            elif method == "prompts/list":
                return _make_response(req_id, {"prompts": []})

            elif method == "ping":
                return _make_response(req_id)

            else:
                return _make_error(req_id, METHOD_NOT_FOUND, f"Unknown method: {method}")

        except McpError as exc:
            return _make_error(req_id, exc.code, exc.message)
        except Exception as exc:
            log.exception("mcp_request_failed", method=method)
            return _make_error(req_id, INTERNAL_ERROR, str(exc))


# ─── SSE Transport ──────────────────────────────────────────────────────────

class SseMcpTransport:
    """MCP transport over Server-Sent Events."""

    def __init__(self, server: McpServer) -> None:
        self.server = server
        self._clients: dict[str, asyncio.Queue[dict[str, Any]]] = {}

    async def connect(self, client_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Register a new SSE client."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._clients[client_id] = queue
        log.info("mcp_sse_client_connected", client_id=client_id)
        return queue

    def disconnect(self, client_id: str) -> None:
        """Remove an SSE client."""
        self._clients.pop(client_id, None)
        log.info("mcp_sse_client_disconnected", client_id=client_id)

    async def handle_message(
        self,
        client_id: str,
        message: dict[str, Any],
        db_session: Any = None,
        workspace_id: str | None = None,
    ) -> None:
        """Process an incoming message and send response via SSE."""
        response = await self.server.handle_request(message, db_session, workspace_id)
        queue = self._clients.get(client_id)
        if queue:
            await queue.put(response)

    async def send_event(self, client_id: str, event: dict[str, Any]) -> None:
        """Send a server-initiated event."""
        queue = self._clients.get(client_id)
        if queue:
            await queue.put(event)


# ─── Stdio Transport ────────────────────────────────────────────────────────

class StdioMcpTransport:
    """MCP transport over standard input/output."""

    def __init__(self, server: McpServer) -> None:
        self.server = server

    async def run(self, db_session: Any = None, workspace_id: str | None = None) -> None:
        """Run the stdio MCP server loop."""
        import sys

        await self.server.initialize()
        log.info("mcp_stdio_server_started")

        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                except json.JSONDecodeError as exc:
                    resp = _make_error(None, PARSE_ERROR, f"Invalid JSON: {exc}")
                    self._write(resp)
                    continue

                response = await self.server.handle_request(request, db_session, workspace_id)
                self._write(response)

            except Exception as exc:
                log.exception("mcp_stdio_loop_error")
                self._write(_make_error(None, INTERNAL_ERROR, str(exc)))

    def _write(self, message: dict[str, Any]) -> None:
        """Write a message to stdout."""
        import sys

        line = json.dumps(message) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()


# ─── Factory ────────────────────────────────────────────────────────────────

_server_instance: McpServer | None = None


def get_mcp_server() -> McpServer:
    """Get or create the singleton MCP server."""
    global _server_instance
    if _server_instance is None:
        _server_instance = McpServer()
    return _server_instance


@asynccontextmanager
async def mcp_sse_transport() -> AsyncIterator[SseMcpTransport]:
    """Context manager for SSE MCP transport."""
    server = get_mcp_server()
    transport = SseMcpTransport(server)
    try:
        yield transport
    finally:
        for client_id in list(transport._clients.keys()):
            transport.disconnect(client_id)