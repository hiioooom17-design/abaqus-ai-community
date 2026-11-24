"""MCP server for a running Abaqus/CAE session."""

from __future__ import annotations

import base64
import json
import os
import uuid
from typing import Any

import anyio
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, ImageContent, TextContent, ToolAnnotations

from .client import AbaqusBridgeClient, BridgeError


mcp = MCPServer(
    "abaqus-control-mcp",
    version="2.0.0",
    instructions="Community edition: read-only session discovery with ping. No remote Python execution.",
)


def _bridge() -> AbaqusBridgeClient:
    return AbaqusBridgeClient(
        host=os.environ.get("ABAQUS_MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("ABAQUS_MCP_PORT", "48152")),
        timeout=float(os.environ.get("ABAQUS_MCP_TIMEOUT", "120")),
    )


def _result(data: dict[str, Any], *, error: bool = False, image_data: str | None = None) -> CallToolResult:
    content = [TextContent(text=json.dumps(data, ensure_ascii=False, default=str))]
    if image_data is not None:
        content.append(ImageContent(data=image_data, mimeType="image/png"))
    return CallToolResult(
        content=content,
        structuredContent=data,
        isError=error,
    )


def _bridge_error(exc: Exception) -> dict[str, Any]:
    data: dict[str, Any] = {"ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}}
    if isinstance(exc, BridgeError):
        data["executionId"] = exc.execution_id
        data["state"] = exc.state
        data["error"]["type"] = exc.error_type
    return data


@mcp.tool(
    description="Check the active Abaqus/CAE connection and return its session details.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True),
)
async def ping() -> CallToolResult:
    try:
        session = await anyio.to_thread.run_sync(_bridge().ping)
    except Exception as exc:
        return _result(_bridge_error(exc), error=True)
    return _result({"ok": True, "executionId": session.get("executionId") or session.get("requestId"), "session": session})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
