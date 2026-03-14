"""Memoria a corto plazo basada en archivos Markdown.

Gestiona los archivos de identidad, diarios y memoria curada.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any


class ShortTermMemory:
    """Lee y escribe la memoria Markdown del agente."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.identity_dir = workspace / "identity"
        self.memory_dir = workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.identity_dir.mkdir(parents=True, exist_ok=True)

    # --- Archivos de identidad ---

    def _read_md(self, path: Path) -> str | None:
        """Lee un archivo .md si existe."""
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def _write_md(self, path: Path, content: str) -> None:
        """Escribe un archivo .md."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def load_soul(self) -> str | None:
        return self._read_md(self.identity_dir / "SOUL.md")

    def load_identity(self) -> str | None:
        return self._read_md(self.identity_dir / "IDENTITY.md")

    def load_agents(self) -> str | None:
        return self._read_md(self.identity_dir / "AGENTS.md")

    def load_user(self) -> str | None:
        return self._read_md(self.identity_dir / "USER.md")

    def load_tools(self) -> str | None:
        return self._read_md(self.identity_dir / "TOOLS.md")

    def load_bootstrap(self) -> str | None:
        return self._read_md(self.identity_dir / "BOOTSTRAP.md")

    def load_heartbeat(self) -> str | None:
        return self._read_md(self.workspace / "HEARTBEAT.md")

    def load_memory(self) -> str | None:
        return self._read_md(self.workspace / "MEMORY.md")

    def save_memory(self, content: str) -> None:
        self._write_md(self.workspace / "MEMORY.md", content)

    def update_user(self, content: str) -> None:
        self._write_md(self.identity_dir / "USER.md", content)

    def update_soul(self, content: str) -> None:
        self._write_md(self.identity_dir / "SOUL.md", content)

    # --- Diarios ---

    def _diary_path(self, day: date) -> Path:
        return self.memory_dir / f"{day.isoformat()}.md"

    def load_diary(self, day: date | None = None) -> str | None:
        day = day or date.today()
        return self._read_md(self._diary_path(day))

    def append_diary(self, entry: str, day: date | None = None) -> None:
        """Añade una entrada al diario del día (append-only)."""
        day = day or date.today()
        path = self._diary_path(day)
        if path.is_file():
            existing = path.read_text(encoding="utf-8")
            content = f"{existing}\n\n{entry}"
        else:
            content = f"# 📝 Diario — {day.isoformat()}\n\n{entry}"
        self._write_md(path, content)

    def load_recent_diaries(self, days: int = 2) -> list[dict[str, Any]]:
        """Carga los diarios de los últimos N días."""
        today = date.today()
        result = []
        for i in range(days):
            day = today - timedelta(days=i)
            content = self.load_diary(day)
            if content:
                result.append({"date": day.isoformat(), "content": content})
        return result

    def list_diaries(self) -> list[str]:
        """Lista todos los archivos de diario disponibles."""
        return sorted(
            [p.stem for p in self.memory_dir.glob("*.md")],
            reverse=True,
        )

    # --- Contexto de arranque ---

    def build_boot_context(self) -> str:
        """Construye el contexto completo que el agente recibe al arrancar.

        Orden: IDENTITY → SOUL → AGENTS → USER → TOOLS → Diarios recientes → MEMORY
        """
        parts: list[str] = []

        identity = self.load_identity()
        if identity:
            parts.append(identity)

        soul = self.load_soul()
        if soul:
            parts.append(soul)

        agents = self.load_agents()
        if agents:
            parts.append(agents)

        user = self.load_user()
        if user:
            parts.append(user)

        tools = self.load_tools()
        if tools:
            parts.append(tools)

        # Diarios recientes
        diaries = self.load_recent_diaries()
        if diaries:
            diary_text = "\n\n---\n\n".join(
                f"## Diario {d['date']}\n\n{d['content']}" for d in diaries
            )
            parts.append(f"# 📝 Diarios recientes\n\n{diary_text}")

        memory = self.load_memory()
        if memory:
            parts.append(memory)

        return "\n\n---\n\n".join(parts)

    def needs_bootstrap(self) -> bool:
        """Verifica si es la primera vez (USER.md sin rellenar)."""
        user = self.load_user()
        if not user:
            return True
        return "**Nombre**: —" in user
