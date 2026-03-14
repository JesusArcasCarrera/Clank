"""Registro de herramientas del agente."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Registro global de herramientas
TOOL_REGISTRY: dict[str, type[Tool]] = {}


class Tool(ABC):
    """Interfaz base para herramientas del agente."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def parameters(self) -> dict[str, Any]: ...

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any: ...

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": self.parameters(),
            },
        }


def register_tool(cls: type[Tool]) -> type[Tool]:
    instance = cls()
    TOOL_REGISTRY[instance.name()] = cls
    return cls


# Importar herramientas para que se registren
from clank.tools.code_exec import RunCode  # noqa: E402, F401
from clank.tools.shell import ShellCommand  # noqa: E402, F401
from clank.tools.filesystem import ReadFile, WriteFile, ListDir  # noqa: E402, F401
