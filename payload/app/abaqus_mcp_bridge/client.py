"""Client used by the MCP server to call the Abaqus-side socket agent."""

from __future__ import annotations

import socket
import os
import re
import math
import uuid
from dataclasses import dataclass
from typing import Any

from .protocol import read_message, send_message


class BridgeError(RuntimeError):
    def __init__(self, message: str, execution_id: str, state: str = "UNKNOWN", error_type: str = "BridgeError"):
        super().__init__(message)
        self.execution_id = execution_id
        self.state = state
        self.error_type = error_type


@dataclass(frozen=True)
class AbaqusBridgeClient:
    host: str = "127.0.0.1"
    port: int = 48152
    timeout: float = 60.0

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.host != "127.0.0.1":
            raise ValueError("only local IPv4 loopback is supported")
        if not math.isfinite(self.timeout) or not 0 < self.timeout <= 300:
            raise ValueError("invalid timeout")
        token = os.environ.get("ABAQUS_MCP_TOKEN", "")
        if not re.fullmatch(r"[0-9a-f]{64}", token):
            raise ValueError("missing installation token; run installer or connection check")
        if method not in ("ping",):
            raise ValueError("method not allowed")
        request_params = dict(params or {})
        request_params.setdefault("timeout", self.timeout)
        payload = {
            "id": str(uuid.uuid4()),
            "token": token,
            "method": method,
            "params": request_params,
        }
        request_params["executionId"] = payload["id"]
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout + 10.0)
                send_message(sock, payload)
                response = read_message(sock)
        except Exception as exc:
            state = "NOT_STARTED" if isinstance(exc, ConnectionRefusedError) else "UNKNOWN"
            raise BridgeError(str(exc), payload["id"], state, type(exc).__name__) from exc

        if response.get("id") != payload["id"]:
            raise BridgeError("Abaqus agent returned a mismatched response id", payload["id"])
        if not response.get("ok", False):
            error = response.get("error") or {}
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise BridgeError(message or "Abaqus agent returned an error", payload["id"], error.get("state", "UNKNOWN") if isinstance(error, dict) else "UNKNOWN", error.get("type", "BridgeError") if isinstance(error, dict) else "BridgeError")
        result = response.get("result")
        if not isinstance(result, dict):
            raise BridgeError("Abaqus agent returned an invalid result envelope", payload["id"])
        if result.get("executionId") not in (None, payload["id"]):
            raise BridgeError("Abaqus agent returned a mismatched executionId", payload["id"])
        return {**result, "requestId": payload["id"], "executionId": payload["id"]}

    def ping(self) -> dict[str, Any]:
        return self.request("ping")

