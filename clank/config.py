"""Carga de configuración desde YAML y variables de entorno."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    enabled: bool = True
    image: str = "clank-sandbox:latest"
    timeout: int = 30
    memory_limit: str = "256m"
    cpu_limit: float = 0.5
    network: bool = False


class GenerationConfig(BaseModel):
    temperature: float = 0.7
    max_tokens: int = 4096


class WebConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class ClankConfig(BaseModel):
    model: str = "gpt-4o-mini"
    system_prompt: str = "Eres Clank, un asistente inteligente."
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    web: WebConfig = Field(default_factory=WebConfig)


def load_config(path: Path | None = None) -> ClankConfig:
    """Carga configuración desde archivo YAML. Busca config.yaml, luego configs/default.yaml."""
    search_paths = [
        path,
        Path("config.yaml"),
        Path("configs/default.yaml"),
    ]

    data: dict[str, Any] = {}
    for p in search_paths:
        if p and p.exists():
            data = yaml.safe_load(p.read_text()) or {}
            break

    return ClankConfig(**data)
