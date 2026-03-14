"""Memoria a largo plazo basada en embeddings con EmbeddingGemma + ChromaDB.

Permite búsqueda semántica sobre toda la memoria histórica del agente.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Vector store local para memoria semántica persistente."""

    def __init__(
        self,
        workspace: Path,
        model_name: str = "google/embeddinggemma-300m",
        collection_name: str = "clank_memory",
    ) -> None:
        self.workspace = workspace
        self.db_path = workspace / ".vectorstore"
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.collection_name = collection_name

        self._model = None
        self._client = None
        self._collection = None
        self._available = False

        self._try_init()

    def _try_init(self) -> None:
        """Intenta inicializar modelo y ChromaDB. Si falla, la memoria LT queda desactivada."""
        try:
            from sentence_transformers import SentenceTransformer
            import chromadb

            self._model = SentenceTransformer(self.model_name)
            self._client = chromadb.PersistentClient(path=str(self.db_path))
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            logger.info("Memoria a largo plazo inicializada con %s", self.model_name)
        except ImportError as e:
            logger.warning(
                "Memoria a largo plazo no disponible (instala sentence-transformers y chromadb): %s", e
            )
        except Exception as e:
            logger.warning("Error inicializando memoria a largo plazo: %s", e)

    @property
    def available(self) -> bool:
        return self._available

    def _content_id(self, text: str) -> str:
        """Genera un ID determinista basado en el contenido."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Almacena un fragmento de texto con sus embeddings.

        Args:
            text: Texto a almacenar.
            metadata: Metadatos opcionales (fecha, tipo, fuente, etc.).

        Returns:
            True si se almacenó correctamente.
        """
        if not self._available:
            return False

        doc_id = self._content_id(text)
        meta = {"date": date.today().isoformat(), "type": "memory"}
        if metadata:
            meta.update(metadata)

        try:
            embedding = self._model.encode(text).tolist()  # type: ignore[union-attr]
            self._collection.upsert(  # type: ignore[union-attr]
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta],
            )
            return True
        except Exception as e:
            logger.error("Error almacenando en memoria a largo plazo: %s", e)
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Busca en la memoria semántica.

        Args:
            query: Texto de búsqueda.
            n_results: Número máximo de resultados.
            where: Filtro opcional de metadatos de ChromaDB.

        Returns:
            Lista de resultados con text, distance y metadata.
        """
        if not self._available:
            return []

        try:
            query_embedding = self._model.encode(query).tolist()  # type: ignore[union-attr]
            kwargs: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            if where:
                kwargs["where"] = where

            results = self._collection.query(**kwargs)  # type: ignore[union-attr]

            output = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    output.append({
                        "text": doc,
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    })
            return output
        except Exception as e:
            logger.error("Error buscando en memoria a largo plazo: %s", e)
            return []

    def index_diary(self, diary_path: Path) -> int:
        """Indexa un diario completo dividiéndolo en párrafos.

        Returns:
            Número de fragmentos indexados.
        """
        if not self._available or not diary_path.is_file():
            return 0

        content = diary_path.read_text(encoding="utf-8")
        day = diary_path.stem  # YYYY-MM-DD

        # Dividir por párrafos (doble salto de línea)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        # Filtrar encabezados sueltos y fragmentos muy cortos
        paragraphs = [p for p in paragraphs if len(p) > 30 and not p.startswith("# ")]

        count = 0
        for para in paragraphs:
            stored = self.store(para, metadata={"date": day, "type": "diary", "source": diary_path.name})
            if stored:
                count += 1

        return count

    def index_all_diaries(self, memory_dir: Path) -> int:
        """Indexa todos los diarios del directorio de memoria."""
        total = 0
        for path in sorted(memory_dir.glob("*.md")):
            total += self.index_diary(path)
        return total

    def count(self) -> int:
        """Número total de documentos en el vector store."""
        if not self._available:
            return 0
        return self._collection.count()  # type: ignore[union-attr]
