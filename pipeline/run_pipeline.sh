#!/bin/bash

# pipeline de verificacion para infraestructura
# ejecuta analisis estatico, pruebas contractuales, integracion y e2e

set -e

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$PIPELINE_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# fase 1: analisis estatico
run_static_analysis() {
    log_info "ejecutando analisis estatico de codigo..."
    
    cd "$PROJECT_ROOT"
    
    # analisis de python
    log_info "analizando codigo python..."
    if ! python -m flake8 --config=pipeline/configs/.flake8 .; then
        log_error "fallos en analisis de codigo python"
        return 1
    fi
    
    cd "$TERRAFORM_DIR"
    
    # tflint
    log_info "ejecutando tflint..."
    if ! tflint --config="$PIPELINE_DIR/configs/.tflint.hcl"; then
        log_error "tflint encontro problemas"
        return 1
    fi
    
    # terraform compliance
    log_info "verificando compliance policies..."
    if ! terraform-compliance -p "$PIPELINE_DIR/policies" -f .; then
        log_error "violaciones de politicas encontradas"
        return 1
    fi
    
    log_info "analisis estatico completado exitosamente"
}

# fase 2: pruebas contractuales
run_contract_tests() {
    log_info "ejecutando pruebas contractuales..."
    
    cd "$PIPELINE_DIR"
    
    # iniciar servicios mock
    docker-compose -f docker-compose.test.yml up -d mock-services
    sleep 5
    
    # ejecutar pruebas pact
    if ! python -m pytest tests/contract/ -v; then
        log_error "pruebas contractuales fallaron"
        docker-compose -f docker-compose.test.yml down
        return 1
    fi
    
    # validar contratos generados
    if ! ./scripts/validate_contracts.sh; then
        log_error "validacion de contratos fallo"
        docker-compose -f docker-compose.test.yml down
        return 1
    fi
    
    docker-compose -f docker-compose.test.yml down
    log_info "pruebas contractuales completadas"
}

# fase 3: pruebas de integracion
run_integration_tests() {
    log_info "ejecutando pruebas de integracion..."
    
    # crear workspace aislado
    WORKSPACE_DIR="/tmp/terraform-test-$(date +%s)"
    mkdir -p "$WORKSPACE_DIR"
    cp -r "$TERRAFORM_DIR"/* "$WORKSPACE_DIR/"
    
    cd "$WORKSPACE_DIR"
    
    # terraform init
    if ! terraform init -backend=false; then
        log_error "terraform init fallo"
        rm -rf "$WORKSPACE_DIR"
        return 1
    fi
    
    # terraform validate
    if ! terraform validate; then
        log_error "terraform validate fallo"
        rm -rf "$WORKSPACE_DIR"
        return 1
    fi
    
    # terraform plan
    if ! terraform plan -out=tfplan; then
        log_error "terraform plan fallo"
        rm -rf "$WORKSPACE_DIR"
        return 1
    fi
    
    # validar outputs esperados
    cd "$PIPELINE_DIR"
    if ! python scripts/validate_terraform_outputs.py "$WORKSPACE_DIR/tfplan"; then
        log_error "validacion de outputs terraform fallo"
        rm -rf "$WORKSPACE_DIR"
        return 1
    fi
    
    rm -rf "$WORKSPACE_DIR"
    log_info "pruebas de integracion completadas"
}

# fase 4: pruebas end-to-end
run_e2e_tests() {
    log_info "ejecutando pruebas end-to-end..."
    
    cd "$PIPELINE_DIR"
    
    # levantar servicios completos
    docker-compose -f docker-compose.e2e.yml up -d
    
    # esperar a que servicios esten listos
    ./scripts/wait_for_services.sh
    
    # ejecutar pruebas e2e
    if ! python -m pytest tests/e2e/ -v; then
        log_error "pruebas e2e fallaron"
        docker-compose -f docker-compose.e2e.yml logs
        docker-compose -f docker-compose.e2e.yml down
        return 1
    fi
    
    docker-compose -f docker-compose.e2e.yml down
    log_info "pruebas end-to-end completadas"
}

# ejecutar pipeline completo
main() {
    log_info "iniciando pipeline de verificacion"
    echo "====================================="
    
    # verificar dependencias
    if ! command -v terraform &> /dev/null; then
        log_error "terraform no esta instalado"
        exit 1
    fi
    
    if ! command -v tflint &> /dev/null; then
        log_error "tflint no esta instalado"
        exit 1
    fi
    
    if ! command -v terraform-compliance &> /dev/null; then
        log_error "terraform-compliance no esta instalado"
        exit 1
    fi
    
    # ejecutar fases
    run_static_analysis || exit 1
    echo "====================================="
    
    run_contract_tests || exit 1
    echo "====================================="
    
    run_integration_tests || exit 1
    echo "====================================="
    
    run_e2e_tests || exit 1
    echo "====================================="
    
    log_info "pipeline completado exitosamente"
}

# permitir ejecutar fases individuales
case "${1:-all}" in
    "static")
        run_static_analysis
        ;;
    "contract")
        run_contract_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "e2e")
        run_e2e_tests
        ;;
    "all"|"")
        main
        ;;
    *)
        echo "uso: $0 [static|contract|integration|e2e|all]"
        exit 1
        ;;
esac 