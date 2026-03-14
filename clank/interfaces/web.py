"""Interfaz web con Chainlit."""

from __future__ import annotations

import chainlit as cl

from clank.agent import Agent
from clank.config import load_config


@cl.on_chat_start
async def on_start() -> None:
    config = load_config()
    agent = Agent(config=config)
    cl.user_session.set("agent", agent)
    await cl.Message(
        content=f"**Clank** conectado. Modelo: `{config.model}`\n\nEscribe lo que necesites."
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent: Agent = cl.user_session.get("agent")  # type: ignore[assignment]

    msg = cl.Message(content="")
    await msg.send()

    try:
        for token in agent.chat_stream(message.content):
            await msg.stream_token(token)
    except Exception as e:
        msg.content = f"Error: {e}"

    await msg.update()
