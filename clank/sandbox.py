"""Ejecución aislada de código y comandos en contenedores Docker."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Intentar importar docker; si no está disponible, modo fallback local
try:
    import docker

    _docker_available = True
except ImportError:
    _docker_available = False

_SANDBOX_IMAGE = "clank-sandbox:latest"


def _get_client() -> Any:
    if not _docker_available:
        return None
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        return None


def run_in_sandbox(code: str, *, timeout: int = 30) -> dict[str, Any]:
    """Ejecuta código Python en un contenedor Docker aislado."""
    client = _get_client()

    if client is None:
        return _run_local_fallback(code, timeout=timeout)

    try:
        result = client.containers.run(
            _SANDBOX_IMAGE,
            command=["python3", "-c", code],
            remove=True,
            network_disabled=True,
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            timeout=timeout,
            stdout=True,
            stderr=True,
        )
        output = result.decode("utf-8", errors="replace")
        return {"status": "ok", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_shell_in_sandbox(command: str, *, timeout: int = 30) -> dict[str, Any]:
    """Ejecuta un comando shell en un contenedor Docker aislado."""
    client = _get_client()

    if client is None:
        return _run_shell_local_fallback(command, timeout=timeout)

    try:
        result = client.containers.run(
            _SANDBOX_IMAGE,
            command=["sh", "-c", command],
            remove=True,
            network_disabled=True,
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            timeout=timeout,
            stdout=True,
            stderr=True,
        )
        output = result.decode("utf-8", errors="replace")
        return {"status": "ok", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _run_local_fallback(code: str, *, timeout: int = 30) -> dict[str, Any]:
    """Fallback: ejecutar localmente cuando Docker no está disponible."""
    import subprocess

    logger.warning("Docker no disponible, ejecutando localmente (sin aislamiento)")
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": output,
            "warning": "Ejecutado localmente (Docker no disponible)",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _run_shell_local_fallback(command: str, *, timeout: int = 30) -> dict[str, Any]:
    """Fallback: ejecutar shell localmente cuando Docker no está disponible."""
    import subprocess

    logger.warning("Docker no disponible, ejecutando shell localmente (sin aislamiento)")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": output,
            "warning": "Ejecutado localmente (Docker no disponible)",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
