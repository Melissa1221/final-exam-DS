#!/bin/bash

set -e

# configuración
REGISTRY_HOST="localhost:5000"
PROJECT_NAME="microservices"
VERSION="${1:-latest}"

# función para logging
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# verificar docker
check_docker() {
    log "verificando docker..."
    if ! command -v docker &> /dev/null; then
        echo "error: docker no está instalado"
        exit 1
    fi
    log "docker ok"
}

# iniciar registry local
start_registry() {
    log "verificando registry local..."
    if ! docker ps | grep -q "registry:2"; then
        log "iniciando registry local..."
        docker run -d -p 5000:5000 --restart=always --name registry registry:2
        sleep 3
    else
        log "registry ya está ejecutándose"
    fi
    log "registry disponible en $REGISTRY_HOST"
}

# build imagen
build_image() {
    local service_name=$1
    local service_path=$2
    
    log "construyendo $service_name..."
    
    local image_tag="$REGISTRY_HOST/$PROJECT_NAME/$service_name:$VERSION"
    
    docker build -t "$image_tag" "$service_path"
    
    log "build completado: $service_name"
    echo "$image_tag"
}

# push imagen
push_image() {
    local image_tag=$1
    local service_name=$2
    
    log "enviando $service_name al registry..."
    docker push "$image_tag"
    log "push completado: $service_name"
}

# verificar registry
verify_registry() {
    log "verificando imágenes en registry..."
    curl -s "http://$REGISTRY_HOST/v2/_catalog" | grep -q "repositories" || log "advertencia: no se pudo verificar registry"
    log "verificación completada"
}

# función principal
main() {
    log "iniciando pipeline de build y publicación"
    log "versión: $VERSION"
    log "registry: $REGISTRY_HOST"
    
    check_docker
    start_registry
    
    # build servicios
    user_image=$(build_image "user-service" "./user-service")
    product_image=$(build_image "product-service" "./product-service")
    
    # push al registry
    push_image "$user_image" "user-service"
    push_image "$product_image" "product-service"
    
    verify_registry
    
    log "pipeline completado exitosamente"
    log "registry disponible en: http://$REGISTRY_HOST/v2/_catalog"
}

# mostrar ayuda
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    echo "uso: $0 [VERSION]"
    echo ""
    echo "construye y publica las imágenes de microservicios en registry local"
    echo ""
    echo "argumentos:"
    echo "  VERSION    versión de las imágenes (default: latest)"
    echo ""
    exit 0
fi

main 