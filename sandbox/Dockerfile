# Imagen sandbox para ejecución aislada de código
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Paquetes comunes que el usuario podría necesitar
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    requests \
    matplotlib

# Usuario sin privilegios
RUN useradd -m -s /bin/bash sandbox
USER sandbox
WORKDIR /home/sandbox

# Sin red por defecto (se controla al crear el contenedor)
