FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias base del sistema (ajustar luego segun librerias geoespaciales)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala requerimientos si existen
COPY requirements.txt /app/requirements.txt
RUN if [ -f /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# Copia proyecto
COPY . /app

# Comando por defecto (reemplazar cuando exista app backend)
CMD ["python", "-m", "http.server", "8000"]

