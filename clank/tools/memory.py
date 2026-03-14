"""Herramientas de memoria para el agente: recordar, buscar, escribir diario."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clank.memory import MemoryManager
from clank.tools import Tool, register_tool

# Referencia global al memory manager — se inyecta desde el agente al arrancar
_memory: MemoryManager | None = None


def set_memory_manager(manager: MemoryManager) -> None:
    """Inyecta el memory manager para que las herramientas lo usen."""
    global _memory
    _memory = manager


def _get_memory() -> MemoryManager:
    if _memory is None:
        raise RuntimeError("MemoryManager no inicializado. Llama a set_memory_manager() primero.")
    return _memory


@register_tool
class Remember(Tool):
    """Almacena un hecho importante en la memoria curada (corto y largo plazo)."""

    def name(self) -> str:
        return "remember"

    def description(self) -> str:
        return (
            "Guarda un hecho o decisión importante en la memoria persistente. "
            "Se almacena en MEMORY.md (corto plazo) y en el vector store (largo plazo)."
        )

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "El hecho, decisión o información a recordar",
                },
            },
            "required": ["fact"],
        }

    def execute(self, *, fact: str, **_: Any) -> dict[str, Any]:
        mem = _get_memory()
        mem.remember(fact)
        return {"status": "ok", "stored_in": ["MEMORY.md", "vector_store"]}


@register_tool
class Recall(Tool):
    """Busca en la memoria a largo plazo por similitud semántica."""

    def name(self) -> str:
        return "recall"

    def description(self) -> str:
        return (
            "Busca en la memoria histórica usando búsqueda semántica. "
            "Útil para recordar conversaciones pasadas, decisiones o contexto."
        )

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Qué quieres recordar o buscar",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Número máximo de resultados (por defecto 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, *, query: str, n_results: int = 5, **_: Any) -> dict[str, Any]:
        mem = _get_memory()
        results = mem.recall(query, n_results=n_results)
        return {"query": query, "results": results, "count": len(results)}


@register_tool
class WriteLog(Tool):
    """Escribe una entrada en el diario del día."""

    def name(self) -> str:
        return "write_log"

    def description(self) -> str:
        return "Escribe una entrada en el diario del día (append-only). Se indexa automáticamente."

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entry": {
                    "type": "string",
                    "description": "La entrada a escribir en el diario",
                },
            },
            "required": ["entry"],
        }

    def execute(self, *, entry: str, **_: Any) -> dict[str, Any]:
        mem = _get_memory()
        mem.log(entry)
        return {"status": "ok", "logged": True}


@register_tool
class MemoryStatus(Tool):
    """Muestra el estado del sistema de memoria."""

    def name(self) -> str:
        return "memory_status"

    def description(self) -> str:
        return "Muestra el estado del sistema de memoria (diarios, vector store, bootstrap)."

    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **_: Any) -> dict[str, Any]:
        mem = _get_memory()
        return mem.status()
