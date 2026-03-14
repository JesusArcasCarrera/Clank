"""Núcleo del agente: gestiona conversación, herramientas y llamadas al LLM vía LiteLLM."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

import litellm

from clank.config import ClankConfig
from clank.memory import MemoryManager
from clank.tools import TOOL_REGISTRY, Tool
from clank.tools.memory import set_memory_manager

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str  # system, user, assistant, tool
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            d["name"] = self.name
        return d


@dataclass
class Agent:
    """Agente conversacional con soporte de herramientas y memoria persistente."""

    config: ClankConfig
    history: list[Message] = field(default_factory=list)
    tools: dict[str, Tool] = field(default_factory=dict)
    memory: MemoryManager = field(init=False)

    def __post_init__(self) -> None:
        # Inicializar memoria
        workspace = Path(self.config.workspace_dir)
        self.memory = MemoryManager(
            workspace=workspace,
            embedding_model=self.config.memory.embedding_model,
        )

        # Construir system prompt enriquecido con contexto de memoria
        boot_context = self.memory.boot_context()
        system_prompt = self.config.system_prompt
        if boot_context:
            system_prompt = f"{system_prompt}\n\n---\n\n{boot_context}"

        self.history.append(Message(role="system", content=system_prompt))
        self.tools = {name: tool_cls() for name, tool_cls in TOOL_REGISTRY.items()}

        # Inyectar memory manager en las herramientas de memoria
        set_memory_manager(self.memory)

        if self.memory.needs_bootstrap():
            logger.info("Primera ejecución detectada — modo bootstrap activo")

    def _tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self.tools.values()]

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if not tool:
            return json.dumps({"error": f"Herramienta '{name}' no encontrada"})
        try:
            result = tool.execute(**arguments)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def chat(self, user_input: str) -> str:
        """Envía un mensaje y devuelve la respuesta final del agente."""
        self.history.append(Message(role="user", content=user_input))

        # Bucle de herramientas: el agente puede llamar herramientas iterativamente
        for _ in range(10):  # máximo 10 iteraciones de herramientas
            response = litellm.completion(
                model=self.config.model,
                messages=[m.to_dict() for m in self.history],
                tools=self._tool_schemas() or None,
                temperature=self.config.generation.temperature,
                max_tokens=self.config.generation.max_tokens,
            )

            choice = response.choices[0]
            msg = choice.message

            # Guardar respuesta del asistente
            assistant_msg = Message(
                role="assistant",
                content=msg.content,
                tool_calls=[tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None,
            )
            self.history.append(assistant_msg)

            # Si no hay tool_calls, hemos terminado
            if not msg.tool_calls:
                return msg.content or ""

            # Ejecutar cada herramienta y añadir resultados
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                result = self._execute_tool(fn_name, fn_args)
                self.history.append(
                    Message(role="tool", content=result, tool_call_id=tc.id, name=fn_name)
                )

        return "Se alcanzó el límite de iteraciones de herramientas."

    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """Versión streaming del chat. Yield de tokens parciales."""
        self.history.append(Message(role="user", content=user_input))

        for _ in range(10):
            response = litellm.completion(
                model=self.config.model,
                messages=[m.to_dict() for m in self.history],
                tools=self._tool_schemas() or None,
                temperature=self.config.generation.temperature,
                max_tokens=self.config.generation.max_tokens,
                stream=True,
            )

            content_parts: list[str] = []
            tool_calls_acc: dict[int, dict[str, Any]] = {}

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                    yield delta.content
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": tc_delta.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        if tc_delta.id:
                            tool_calls_acc[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_acc[idx]["function"]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_acc[idx]["function"]["arguments"] += (
                                    tc_delta.function.arguments
                                )

            full_content = "".join(content_parts) or None
            tool_calls_list = list(tool_calls_acc.values()) if tool_calls_acc else None

            self.history.append(
                Message(role="assistant", content=full_content, tool_calls=tool_calls_list)
            )

            if not tool_calls_list:
                return

            for tc in tool_calls_list:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                result = self._execute_tool(fn_name, fn_args)
                yield f"\n🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)})\n"
                self.history.append(
                    Message(role="tool", content=result, tool_call_id=tc["id"], name=fn_name)
                )

        yield "\nSe alcanzó el límite de iteraciones de herramientas."

    def reset(self) -> None:
        """Limpia el historial manteniendo el system prompt + contexto de memoria."""
        boot_context = self.memory.boot_context()
        system_prompt = self.config.system_prompt
        if boot_context:
            system_prompt = f"{system_prompt}\n\n---\n\n{boot_context}"
        self.history = [Message(role="system", content=system_prompt)]
