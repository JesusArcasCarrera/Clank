# Clank

Agente LLM sencillo tipo OpenClaw con soporte multi-proveedor, interfaz CLI/web y ejecución aislada en Docker.

## Características

- **Multi-proveedor**: Soporta 100+ modelos (OpenAI, Anthropic, Groq, Ollama, etc.) vía LiteLLM
- **CLI interactivo**: Interfaz de terminal con Rich y streaming
- **Interfaz web**: Chat web con Chainlit
- **Ejecución aislada**: Código y comandos se ejecutan en contenedores Docker
- **Herramientas**: Ejecución de código Python, shell, lectura/escritura de archivos

## Instalación

```bash
# Clonar e instalar
git clone https://github.com/JesusArcasCarrera/Clank.git
cd Clank
pip install -e .

# Configurar API keys
cp .env.example .env
# Editar .env con tus claves
```

## Uso

### CLI

```bash
# Con modelo por defecto (gpt-4o-mini)
clank

# Con otro modelo
clank --model claude-sonnet-4-20250514
clank --model ollama/llama3
clank --model groq/llama3-70b-8192
```

### Interfaz Web

```bash
clank --web
# Abre http://localhost:8000
```

### Docker

```bash
# Construir y lanzar todo
docker compose up

# Solo construir la sandbox
docker build -t clank-sandbox:latest ./sandbox
```

## Configuración

Copia `configs/default.yaml` a `config.yaml` y ajusta:

```yaml
model: "gpt-4o-mini"          # Cualquier modelo de LiteLLM
sandbox:
  enabled: true                # Ejecutar código en Docker
  timeout: 30                  # Timeout por ejecución
  network: false               # Sin acceso a red en sandbox
```

## Estructura

```
clank/
├── agent.py              # Núcleo del agente (conversación + herramientas)
├── config.py             # Carga de configuración
├── sandbox.py            # Ejecución Docker aislada
├── cli.py                # Interfaz CLI con Rich
├── tools/
│   ├── code_exec.py      # Ejecutar código Python
│   ├── shell.py          # Ejecutar comandos shell
│   └── filesystem.py     # Leer/escribir archivos
└── interfaces/
    └── web.py            # Interfaz Chainlit
```

## Modelos soportados

Cualquier modelo compatible con [LiteLLM](https://docs.litellm.ai/docs/providers):

| Proveedor | Ejemplo |
|-----------|---------|
| OpenAI | `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001` |
| Ollama (local) | `ollama/llama3`, `ollama/mistral` |
| Groq | `groq/llama3-70b-8192` |
| Together | `together_ai/meta-llama/Llama-3-70b` |
