"""Gestor unificado de memoria: coordina corto plazo (MD) y largo plazo (embeddings)."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

from clank.memory.long_term import LongTermMemory
from clank.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """Fachada que unifica ambos sistemas de memoria."""

    def __init__(
        self,
        workspace: Path,
        embedding_model: str = "google/embeddinggemma-300m",
    ) -> None:
        self.workspace = workspace
        self.short = ShortTermMemory(workspace)
        self.long = LongTermMemory(workspace, model_name=embedding_model)

    # --- Arranque ---

    def boot_context(self) -> str:
        """Genera el contexto completo de arranque del agente (system prompt + memoria)."""
        return self.short.build_boot_context()

    def needs_bootstrap(self) -> bool:
        return self.short.needs_bootstrap()

    # --- Heartbeat ---

    def heartbeat(self) -> str | None:
        """Lee HEARTBEAT.md para tareas recurrentes."""
        return self.short.load_heartbeat()

    # --- Diario ---

    def log(self, entry: str) -> None:
        """Escribe en el diario de hoy y lo indexa en largo plazo."""
        self.short.append_diary(entry)
        if self.long.available:
            self.long.store(entry, metadata={
                "date": date.today().isoformat(),
                "type": "diary",
            })

    # --- Memoria curada ---

    def remember(self, fact: str) -> None:
        """Almacena un hecho importante en MEMORY.md y en el vector store."""
        # Añadir a MEMORY.md
        current = self.short.load_memory() or ""
        timestamp = date.today().isoformat()
        updated = f"{current}\n\n## {timestamp}\n- {fact}"
        self.short.save_memory(updated)

        # Indexar en largo plazo
        if self.long.available:
            self.long.store(fact, metadata={
                "date": timestamp,
                "type": "curated_memory",
            })

    def recall(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Busca en la memoria a largo plazo por similitud semántica.

        Falls back to returning recent diaries if embeddings aren't available.
        """
        if self.long.available:
            return self.long.search(query, n_results=n_results)

        # Fallback: devolver diarios recientes como contexto
        diaries = self.short.load_recent_diaries(days=7)
        return [{"text": d["content"], "metadata": {"date": d["date"]}} for d in diaries]

    # --- Identidad ---

    def update_user_profile(self, content: str) -> None:
        self.short.update_user(content)

    def update_soul(self, content: str) -> None:
        self.short.update_soul(content)

    # --- Indexación ---

    def reindex(self) -> int:
        """Reindexa toda la memoria en el vector store."""
        if not self.long.available:
            logger.warning("No se puede reindexar: memoria a largo plazo no disponible")
            return 0
        return self.long.index_all_diaries(self.short.memory_dir)

    # --- Estado ---

    def status(self) -> dict[str, Any]:
        """Estado del sistema de memoria."""
        return {
            "short_term": {
                "diaries": len(self.short.list_diaries()),
                "has_memory": self.short.load_memory() is not None,
                "needs_bootstrap": self.needs_bootstrap(),
            },
            "long_term": {
                "available": self.long.available,
                "documents": self.long.count() if self.long.available else 0,
                "model": self.long.model_name,
            },
        }
