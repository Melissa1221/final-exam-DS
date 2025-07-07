# BUild stage
FROM python:3.11-slim as builder

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /build

# Copiar solo requirements.txt primero (para optimizar cache de Docker)
COPY requirements.txt .

# Crear entorno virtual y instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias en el venv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar solo las dependencias mínimas de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copiar el entorno virtual desde el stage builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Crear directorios de aplicación y data
WORKDIR /app
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Copiar script de entrypoint
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh

# Copiar código de aplicación
COPY app/ /app/
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

# Exponer puerto
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Usar entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto
CMD ["python", "main.py"] 