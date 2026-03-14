# Dockerfile principal para ejecutar Clank como servicio
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copiar código fuente
COPY . .
RUN pip install --no-cache-dir -e .

# Puerto para interfaz web
EXPOSE 8000

# CLI por defecto, web con --web
ENTRYPOINT ["python", "-m", "clank.cli"]
