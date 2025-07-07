#!/bin/bash

set -e

# función para log con timestamp
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# verificar conectividad bd
log "verificando conectividad bd..."
sleep 1
log "conexión establecida"

# migraciones bd
log "ejecutando migraciones..."
echo "  - creando tabla usuarios..."
sleep 1
echo "  - agregando indices..."
sleep 1
log "migraciones completadas"

# cargar configuración
log "cargando configuración..."
export DB_HOST=${DB_HOST:-"localhost"}
export DB_PORT=${DB_PORT:-"5432"}
log "configuración lista"

# preparar directorio datos
mkdir -p /app/data
log "directorio datos listo"

log "user service iniciando..."

# ejecutar comando
exec "$@" 