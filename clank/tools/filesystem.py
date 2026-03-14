"""Herramientas de sistema de archivos (lectura local, no sandbox)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clank.tools import Tool, register_tool

# Directorio de trabajo permitido (se puede ajustar)
ALLOWED_ROOT = Path.cwd()


def _safe_path(path_str: str) -> Path:
    """Resuelve y valida que la ruta esté dentro del directorio permitido."""
    p = (ALLOWED_ROOT / path_str).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT.resolve())):
        raise PermissionError(f"Acceso denegado fuera de {ALLOWED_ROOT}")
    return p


@register_tool
class ReadFile(Tool):
    def name(self) -> str:
        return "read_file"

    def description(self) -> str:
        return "Lee el contenido de un archivo local."

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta relativa al archivo"},
            },
            "required": ["path"],
        }

    def execute(self, *, path: str, **_: Any) -> dict[str, Any]:
        p = _safe_path(path)
        if not p.is_file():
            return {"error": f"No es un archivo: {path}"}
        content = p.read_text(errors="replace")
        if len(content) > 50_000:
            content = content[:50_000] + "\n... (truncado)"
        return {"path": str(p.relative_to(ALLOWED_ROOT)), "content": content}


@register_tool
class WriteFile(Tool):
    def name(self) -> str:
        return "write_file"

    def description(self) -> str:
        return "Escribe contenido en un archivo local."

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta relativa al archivo"},
                "content": {"type": "string", "description": "Contenido a escribir"},
            },
            "required": ["path", "content"],
        }

    def execute(self, *, path: str, content: str, **_: Any) -> dict[str, Any]:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"path": str(p.relative_to(ALLOWED_ROOT)), "bytes_written": len(content)}


@register_tool
class ListDir(Tool):
    def name(self) -> str:
        return "list_dir"

    def description(self) -> str:
        return "Lista el contenido de un directorio."

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ruta relativa al directorio",
                    "default": ".",
                },
            },
        }

    def execute(self, *, path: str = ".", **_: Any) -> dict[str, Any]:
        p = _safe_path(path)
        if not p.is_dir():
            return {"error": f"No es un directorio: {path}"}
        entries = []
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"path": str(p.relative_to(ALLOWED_ROOT)), "entries": entries}
