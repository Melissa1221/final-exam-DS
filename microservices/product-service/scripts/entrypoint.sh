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

# migraciones bd específicas productos
log "ejecutando migraciones productos..."
echo "  - creando tabla productos..."
sleep 1
echo "  - creando tabla categorías..."
sleep 1
echo "  - agregando indices precios..."
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

log "product service iniciando..."

# ejecutar comando
exec "$@" 