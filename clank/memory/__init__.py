"""Sistema de memoria dual: corto plazo (Markdown) + largo plazo (embeddings)."""

from clank.memory.short_term import ShortTermMemory
from clank.memory.long_term import LongTermMemory
from clank.memory.manager import MemoryManager

__all__ = ["ShortTermMemory", "LongTermMemory", "MemoryManager"]
