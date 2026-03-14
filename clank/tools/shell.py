"""Herramienta para ejecutar comandos shell en sandbox Docker."""

from __future__ import annotations

from typing import Any

from clank.tools import Tool, register_tool
from clank.sandbox import run_shell_in_sandbox


@register_tool
class ShellCommand(Tool):
    def name(self) -> str:
        return "shell"

    def description(self) -> str:
        return (
            "Ejecuta un comando shell en un contenedor Docker aislado. "
            "Útil para instalar paquetes, listar archivos, etc."
        )

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Comando shell a ejecutar",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos (máx 60)",
                    "default": 30,
                },
            },
            "required": ["command"],
        }

    def execute(self, *, command: str, timeout: int = 30, **_: Any) -> dict[str, Any]:
        timeout = min(timeout, 60)
        return run_shell_in_sandbox(command, timeout=timeout)
