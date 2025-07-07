#!/bin/bash

# script para esperar a que los servicios esten listos
# verifica health checks de todos los servicios e2e

set -e

# configuracion de timeouts
MAX_WAIT=300  # 5 minutos
INTERVAL=10   # 10 segundos

# colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# verificar si un servicio http responde
check_http_service() {
    local name=$1
    local url=$2
    local timeout=${3:-10}
    
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# verificar si un puerto tcp esta abierto
check_tcp_port() {
    local host=$1
    local port=$2
    local timeout=${3:-5}
    
    if timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# esperar por kubernetes master
wait_for_k8s_master() {
    local url="http://localhost:6443/healthz"
    local elapsed=0
    
    log_info "esperando kubernetes master..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_http_service "k8s-master" "$url"; then
            log_info "kubernetes master listo"
            return 0
        fi
        
        log_warn "kubernetes master no listo, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando kubernetes master"
    return 1
}

# esperar por workers
wait_for_k8s_workers() {
    local worker1_url="http://localhost:10250/healthz"
    local worker2_url="http://localhost:10251/healthz"
    local elapsed=0
    
    log_info "esperando kubernetes workers..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_http_service "k8s-worker-1" "$worker1_url" && \
           check_http_service "k8s-worker-2" "$worker2_url"; then
            log_info "kubernetes workers listos"
            return 0
        fi
        
        log_warn "kubernetes workers no listos, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando kubernetes workers"
    return 1
}

# esperar por nginx demo
wait_for_nginx_demo() {
    local url="http://localhost:8080"
    local elapsed=0
    
    log_info "esperando nginx demo..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_http_service "nginx-demo" "$url"; then
            log_info "nginx demo listo"
            return 0
        fi
        
        log_warn "nginx demo no listo, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando nginx demo"
    return 1
}

# esperar por prometheus
wait_for_prometheus() {
    local url="http://localhost:9090/-/healthy"
    local elapsed=0
    
    log_info "esperando prometheus..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_http_service "prometheus" "$url"; then
            log_info "prometheus listo"
            return 0
        fi
        
        log_warn "prometheus no listo, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando prometheus"
    return 1
}

# esperar por grafana
wait_for_grafana() {
    local url="http://localhost:3000/api/health"
    local elapsed=0
    
    log_info "esperando grafana..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_http_service "grafana" "$url" 15; then
            log_info "grafana listo"
            return 0
        fi
        
        log_warn "grafana no listo, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando grafana"
    return 1
}

# esperar por bastion host
wait_for_bastion() {
    local host="localhost"
    local port=2222
    local elapsed=0
    
    log_info "esperando bastion host..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if check_tcp_port "$host" "$port"; then
            log_info "bastion host listo"
            return 0
        fi
        
        log_warn "bastion host no listo, esperando..."
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
    done
    
    log_error "timeout esperando bastion host"
    return 1
}

# verificar que docker compose este funcionando
check_docker_compose() {
    log_info "verificando estado de contenedores..."
    
    if ! docker-compose -f docker-compose.e2e.yml ps --format table; then
        log_error "error obteniendo estado de contenedores"
        return 1
    fi
    
    # verificar que no haya contenedores en estado exit
    local exited_containers
    exited_containers=$(docker-compose -f docker-compose.e2e.yml ps --filter "status=exited" --format table 2>/dev/null | wc -l)
    
    if [ "$exited_containers" -gt 1 ]; then  # header cuenta como 1
        log_warn "hay contenedores que han salido"
        docker-compose -f docker-compose.e2e.yml ps --filter "status=exited"
    fi
    
    return 0
}

# funcion principal
main() {
    log_info "iniciando verificacion de servicios..."
    
    # verificar estado de contenedores
    check_docker_compose
    
    # esperar por cada servicio
    wait_for_k8s_master || exit 1
    wait_for_k8s_workers || exit 1
    wait_for_nginx_demo || exit 1
    wait_for_prometheus || exit 1
    wait_for_grafana || exit 1
    wait_for_bastion || exit 1
    
    log_info "todos los servicios estan listos"
    
    # dar tiempo adicional para estabilizacion
    log_info "esperando estabilizacion de servicios..."
    sleep 30
    
    log_info "servicios estabilizados, listos para pruebas"
}

# ejecutar si es llamado directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 