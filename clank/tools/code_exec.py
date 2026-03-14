"""Herramienta para ejecutar código Python en sandbox Docker."""

from __future__ import annotations

from typing import Any

from clank.tools import Tool, register_tool
from clank.sandbox import run_in_sandbox


@register_tool
class RunCode(Tool):
    def name(self) -> str:
        return "run_code"

    def description(self) -> str:
        return (
            "Ejecuta código Python en un contenedor Docker aislado. "
            "Usa esta herramienta cuando el usuario pida ejecutar código."
        )

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Código Python a ejecutar",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos (máx 60)",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    def execute(self, *, code: str, timeout: int = 30, **_: Any) -> dict[str, Any]:
        timeout = min(timeout, 60)
        return run_in_sandbox(code, timeout=timeout)
