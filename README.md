<div align="center">

# 🤖 Clank

**Agente LLM ligero tipo OpenClaw — multi-proveedor, CLI/Web, sandbox Docker**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![LiteLLM](https://img.shields.io/badge/LLM-LiteLLM-orange?logo=ai)](https://docs.litellm.ai)
[![Docker](https://img.shields.io/badge/sandbox-Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<p>
  <a href="#-inicio-rápido">Inicio rápido</a> •
  <a href="#-características">Características</a> •
  <a href="#-uso">Uso</a> •
  <a href="#-configuración">Configuración</a> •
  <a href="#-arquitectura">Arquitectura</a> •
  <a href="#-contribuir">Contribuir</a>
</p>

---

<img src="https://img.shields.io/badge/100%2B_modelos-soportados-blueviolet?style=for-the-badge" alt="100+ modelos">

</div>

## ✨ Características

| | Característica | Descripción |
|---|---|---|
| 🔀 | **Multi-proveedor** | 100+ modelos vía LiteLLM — OpenAI, Anthropic, Groq, Ollama, Together, etc. |
| 🧠 | **Memoria dual** | Corto plazo (Markdown) + largo plazo (embeddings con EmbeddingGemma + ChromaDB) |
| 💓 | **Heartbeat** | Tareas recurrentes que el agente revisa periódicamente |
| 👤 | **Identidad persistente** | SOUL.md, IDENTITY.md, USER.md — el agente "se lee a sí mismo" al arrancar |
| 💻 | **CLI interactivo** | Terminal con Rich, streaming en tiempo real y autocompletado |
| 🌐 | **Interfaz web** | Chat web con Chainlit, streaming y gestión de sesiones |
| 🐳 | **Sandbox Docker** | Código y shell se ejecutan aislados (sin red, con límites de CPU/RAM) |
| 🔧 | **Herramientas** | Ejecución de Python, comandos shell, lectura/escritura de archivos, memoria |
| ⚙️ | **Configurable** | YAML + variables de entorno, fácil de personalizar |

## 🚀 Inicio rápido

### Requisitos previos

- Python 3.11+
- Docker (opcional, para sandbox aislada)
- API key de al menos un proveedor LLM

### Instalación

```bash
# Clonar e instalar
git clone https://github.com/JesusArcasCarrera/Clank.git
cd Clank
pip install -e .

# Configurar API keys
cp .env.example .env
# Editar .env con tus claves (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

### Primera ejecución

```bash
# Lanzar el CLI
clank

# O con Docker Compose (levanta web + sandbox)
docker compose up
```

## 📖 Uso

### CLI

```bash
# Modelo por defecto (gpt-4o-mini)
clank

# Cambiar modelo sobre la marcha
clank --model claude-sonnet-4-20250514
clank --model ollama/llama3
clank --model groq/llama3-70b-8192
```

**Comandos dentro del chat:**

| Comando | Acción |
|---------|--------|
| `/reset` | Limpiar historial de conversación |
| `/model <nombre>` | Cambiar modelo en caliente |
| `/exit` | Salir |

### Interfaz Web

```bash
clank --web
# Abre http://localhost:8000
```

### Docker

```bash
# Todo junto (web + sandbox aislada)
docker compose up

# Solo la sandbox
docker build -t clank-sandbox:latest ./sandbox
```

## 🧠 Sistema de memoria

Clank tiene un sistema de memoria dual inspirado en OpenClaw:

### Corto plazo — Archivos Markdown

```
workspace/
├── identity/
│   ├── SOUL.md          # 🧠 Personalidad, valores, vibe — el agente "se lee a sí mismo"
│   ├── IDENTITY.md      # 🤖 Nombre, tipo, emoji — ancla de identidad
│   ├── AGENTS.md        # 📋 Reglas de operación, permisos, estilo
│   ├── USER.md          # 👤 Info sobre el usuario (se rellena en bootstrap)
│   ├── TOOLS.md         # 🔧 Config del entorno (SSH, cámaras, servicios)
│   └── BOOTSTRAP.md     # 🚀 Guía de primera conversación (se borra después)
├── HEARTBEAT.md         # 💓 Tareas recurrentes (se revisa cada 30 min)
├── MEMORY.md            # 🧠 Memoria curada a largo plazo
└── memory/
    ├── 2026-03-14.md    # 📝 Diario de hoy (append-only)
    └── 2026-03-13.md    # 📝 Diario de ayer
```

**Al arrancar**, el agente carga: `IDENTITY → SOUL → AGENTS → USER → TOOLS → Diarios recientes → MEMORY`

**Primera vez**: detecta USER.md sin rellenar y entra en modo **bootstrap** (se presenta, conoce al usuario, documenta).

### Largo plazo — Embeddings

- **Modelo**: [EmbeddingGemma](https://ai.google.dev/gemma/docs/embeddinggemma) (308M params, ~200MB RAM, 768 dims)
- **Vector store**: ChromaDB (local, persistente)
- Los diarios y memorias curadas se indexan automáticamente
- Búsqueda semántica: "¿qué me dijo el usuario sobre su proyecto?" → resultados por similitud
- **Opcional**: si no instalas `sentence-transformers` y `chromadb`, funciona solo con MD

### Herramientas de memoria del agente

| Herramienta | Qué hace |
|-------------|----------|
| `remember` | Guarda un hecho en MEMORY.md + vector store |
| `recall` | Búsqueda semántica en toda la memoria histórica |
| `write_log` | Escribe en el diario del día |
| `memory_status` | Muestra estado del sistema de memoria |

## ⚙️ Configuración

Copia `configs/default.yaml` a `config.yaml` y ajusta:

```yaml
model: "gpt-4o-mini"          # Cualquier modelo soportado por LiteLLM

workspace_dir: "workspace"     # Donde vive la identidad y memoria

memory:
  embedding_model: "google/embeddinggemma-300m"  # Modelo para largo plazo
  heartbeat_interval: 30                         # Minutos entre heartbeats

sandbox:
  enabled: true                # Ejecutar código en contenedores Docker
  timeout: 30                  # Segundos máx por ejecución
  memory_limit: "256m"         # Límite de RAM
  cpu_limit: 0.5               # Límite de CPU
  network: false               # Sin acceso a internet en sandbox

generation:
  temperature: 0.7
  max_tokens: 4096

web:
  host: "0.0.0.0"
  port: 8000
```

### Variables de entorno

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
# Para Ollama local no necesitas key
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│               Interfaces                            │
│    ┌─────────────┐       ┌──────────────────┐       │
│    │  CLI (Rich)  │       │  Web (Chainlit)  │       │
│    └──────┬───────┘       └────────┬─────────┘       │
└───────────┼────────────────────────┼─────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────────┐
│            Agent (agent.py)                         │
│   Conversación • Tool loop • Streaming              │
└────────┬───────────────────────────┬────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐   ┌──────────────────────────┐
│   🔧 Herramientas   │   │   🧠 Sistema de Memoria  │
│                     │   │                          │
│  code_exec (Python) │   │  Corto plazo (Markdown)  │
│  shell (bash)       │   │    SOUL · IDENTITY       │
│  filesystem (R/W)   │   │    HEARTBEAT · MEMORY    │
│  remember / recall  │   │    Diarios diarios       │
│  write_log          │   │                          │
└────────┬────────────┘   │  Largo plazo (Embeddings)│
         │                │    EmbeddingGemma 300M   │
         ▼                │    ChromaDB local        │
┌─────────────────────┐   └──────────────────────────┘
│  Sandbox Docker     │
│  Aislado • Sin red  │
└─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│            LiteLLM (multi-proveedor)                │
│   OpenAI • Anthropic • Ollama • Groq • 100+        │
└─────────────────────────────────────────────────────┘
```

### Estructura de archivos

```
Clank/
├── clank/
│   ├── agent.py              # Núcleo del agente (conversación + herramientas)
│   ├── config.py             # Carga de configuración YAML + Pydantic
│   ├── sandbox.py            # Ejecución Docker aislada con fallback local
│   ├── cli.py                # Interfaz CLI con Rich + prompt_toolkit
│   ├── memory/
│   │   ├── __init__.py       # Exports del sistema de memoria
│   │   ├── short_term.py     # Memoria MD (identidad, diarios, MEMORY.md)
│   │   ├── long_term.py      # Embeddings (EmbeddingGemma + ChromaDB)
│   │   └── manager.py        # Fachada unificada de memoria
│   ├── tools/
│   │   ├── __init__.py       # Registro de herramientas
│   │   ├── code_exec.py      # Ejecutar código Python en sandbox
│   │   ├── shell.py          # Ejecutar comandos shell en sandbox
│   │   ├── filesystem.py     # Leer/escribir/listar archivos
│   │   └── memory.py         # remember, recall, write_log, memory_status
│   └── interfaces/
│       └── web.py            # Interfaz Chainlit
├── workspace/
│   ├── identity/
│   │   ├── SOUL.md           # 🧠 Personalidad y valores
│   │   ├── IDENTITY.md       # 🤖 Nombre, tipo, emoji
│   │   ├── AGENTS.md         # 📋 Reglas de operación
│   │   ├── USER.md           # 👤 Perfil del usuario
│   │   ├── TOOLS.md          # 🔧 Config del entorno
│   │   └── BOOTSTRAP.md      # 🚀 Setup inicial
│   ├── HEARTBEAT.md          # 💓 Tareas recurrentes
│   ├── MEMORY.md             # 🧠 Memoria curada
│   └── memory/               # 📝 Diarios diarios (YYYY-MM-DD.md)
├── configs/
│   └── default.yaml          # Configuración por defecto
├── sandbox/
│   └── Dockerfile            # Imagen Docker para sandbox
├── Dockerfile                # Imagen principal de Clank
├── docker-compose.yaml       # Orquestación completa
└── pyproject.toml            # Dependencias y metadata
```

## 🔌 Modelos soportados

Cualquier modelo compatible con [LiteLLM](https://docs.litellm.ai/docs/providers):

| Proveedor | Ejemplo de modelo | API Key |
|-----------|-------------------|---------|
| OpenAI | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| Ollama | `ollama/llama3`, `ollama/mistral` | — (local) |
| Groq | `groq/llama3-70b-8192` | `GROQ_API_KEY` |
| Together | `together_ai/meta-llama/Llama-3-70b` | `TOGETHER_API_KEY` |
| Azure OpenAI | `azure/gpt-4o` | `AZURE_API_KEY` |
| AWS Bedrock | `bedrock/anthropic.claude-3` | AWS credentials |

> [Lista completa de proveedores](https://docs.litellm.ai/docs/providers)

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork del repositorio
2. Crea tu rama (`git checkout -b feature/mi-feature`)
3. Commit de tus cambios (`git commit -m 'feat: añadir mi-feature'`)
4. Push a la rama (`git push origin feature/mi-feature`)
5. Abre un Pull Request

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Lint
ruff check .

# Tests
pytest
```

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

<div align="center">

Hecho con ❤️ por [JesusArcasCarrera](https://github.com/JesusArcasCarrera)

⭐ Si te resulta útil, dale una estrella al repo ⭐

</div>
