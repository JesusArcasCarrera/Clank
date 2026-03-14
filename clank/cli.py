"""Interfaz CLI interactiva con Rich y prompt_toolkit."""

from __future__ import annotations

import argparse
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from clank.agent import Agent
from clank.config import load_config


console = Console()


def print_welcome() -> None:
    console.print(
        Panel(
            "[bold cyan]Clank[/bold cyan] - Agente LLM con ejecución aislada\n"
            "Escribe tu mensaje. Usa [bold]/salir[/bold] para salir, "
            "[bold]/reset[/bold] para limpiar historial.",
            title="Clank v0.1.0",
            border_style="cyan",
        )
    )


def run_cli(agent: Agent) -> None:
    """Bucle principal del CLI interactivo."""
    print_welcome()

    session: PromptSession[str] = PromptSession(history=InMemoryHistory())

    while True:
        try:
            user_input = session.prompt("\n🧑 > ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]¡Hasta luego![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/salir", "/exit", "/quit"):
            console.print("[dim]¡Hasta luego![/dim]")
            break

        if user_input.lower() in ("/reset", "/clear"):
            agent.reset()
            console.print("[dim]Historial limpiado.[/dim]")
            continue

        if user_input.lower() in ("/help", "/ayuda"):
            console.print(
                Panel(
                    "[bold]/salir[/bold] - Salir\n"
                    "[bold]/reset[/bold] - Limpiar historial\n"
                    "[bold]/modelo[/bold] - Ver modelo actual\n"
                    "[bold]/help[/bold] - Esta ayuda",
                    title="Comandos",
                    border_style="blue",
                )
            )
            continue

        if user_input.lower() in ("/modelo", "/model"):
            console.print(f"[dim]Modelo: {agent.config.model}[/dim]")
            continue

        # Streaming de respuesta
        console.print()
        full_response: list[str] = []
        try:
            with Live(Markdown("▌"), console=console, refresh_per_second=10) as live:
                for token in agent.chat_stream(user_input):
                    full_response.append(token)
                    live.update(Markdown("".join(full_response) + "▌"))
                live.update(Markdown("".join(full_response)))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clank - Agente LLM")
    parser.add_argument("--model", "-m", help="Modelo LLM a usar (ej: gpt-4o, claude-sonnet-4-20250514)")
    parser.add_argument("--config", "-c", help="Ruta al archivo de configuración YAML")
    parser.add_argument(
        "--web", action="store_true", help="Iniciar interfaz web (Chainlit)"
    )
    args = parser.parse_args()

    from pathlib import Path

    config = load_config(Path(args.config) if args.config else None)

    if args.model:
        config.model = args.model

    if args.web:
        _launch_web(config)
        return

    agent = Agent(config=config)
    run_cli(agent)


def _launch_web(config: object) -> None:
    """Lanza la interfaz web con Chainlit."""
    import subprocess

    app_path = str(__import__("pathlib").Path(__file__).parent / "interfaces" / "web.py")
    subprocess.run([sys.executable, "-m", "chainlit", "run", app_path, "--host", "0.0.0.0"])


if __name__ == "__main__":
    main()
