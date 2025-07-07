#!/bin/bash

# pipeline simplificado para verificacion de infraestructura
# enfoque kiss - keep it simple stupid

set -e

PROJECT_ROOT="$(pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# colores simples
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# fase 1: analisis estatico basico
static_analysis() {
    echo "=== analisis estatico ==="
    
    # verificar sintaxis python
    echo "verificando codigo python..."
    if python -m py_compile iac/*.py; then
        success "codigo python valido"
    else
        error "errores en codigo python"
        return 1
    fi
    
    cd "$TERRAFORM_DIR"
    
    # terraform validate
    echo "verificando terraform..."
    if terraform init -backend=false > /dev/null 2>&1 && terraform validate; then
        success "terraform valido"
    else
        error "terraform invalido"
        return 1
    fi
    
    # tflint si esta disponible
    if command -v tflint &> /dev/null; then
        echo "ejecutando tflint..."
        if tflint; then
            success "tflint ok"
        else
            error "tflint encontro problemas"
            return 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
}

# fase 2: pruebas contractuales simples
contract_tests() {
    echo "=== pruebas contractuales ==="
    
    # verificar que tenemos pruebas
    if [ ! -f "pipeline/tests/contract/test_simple_contracts.py" ]; then
        error "no se encontraron pruebas contractuales"
        return 1
    fi
    
    # ejecutar pruebas contractuales
    echo "ejecutando pruebas de contrato..."
    cd pipeline
    if python -m pytest tests/contract/test_simple_contracts.py -v --tb=short; then
        success "pruebas contractuales ok"
    else
        error "pruebas contractuales fallaron"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
}

# fase 3: pruebas de integracion terraform
integration_tests() {
    echo "=== pruebas de integracion ==="
    
    # crear workspace temporal
    TEMP_DIR="/tmp/terraform-test-$$"
    mkdir -p "$TEMP_DIR"
    cp -r "$TERRAFORM_DIR"/* "$TEMP_DIR/"
    
    cd "$TEMP_DIR"
    
    echo "generando plan terraform..."
    if terraform init -backend=false > /dev/null 2>&1 && terraform plan -out=tfplan > /dev/null 2>&1; then
        success "plan terraform generado"
    else
        error "fallo al generar plan"
        rm -rf "$TEMP_DIR"
        return 1
    fi
    
    # convertir plan a json para validaciones
    echo "validando plan..."
    if terraform show -json tfplan > plan.json; then
        # validar con script de politicas
        if python "$PROJECT_ROOT/pipeline/policies/security.py" plan.json; then
            success "validaciones de seguridad ok"
        else
            error "validaciones de seguridad fallaron"
            rm -rf "$TEMP_DIR"
            return 1
        fi
        
        # validar outputs
        if python "$PROJECT_ROOT/pipeline/scripts/validate_terraform_outputs.py" tfplan; then
            success "outputs terraform ok"
        else
            error "outputs terraform invalidos"
            rm -rf "$TEMP_DIR"
            return 1
        fi
    else
        error "no se pudo convertir plan a json"
        rm -rf "$TEMP_DIR"
        return 1
    fi
    
    rm -rf "$TEMP_DIR"
    cd "$PROJECT_ROOT"
}

# fase 4: pruebas e2e simples
e2e_tests() {
    echo "=== pruebas end-to-end ==="
    
    cd pipeline
    
    # levantar servicios de prueba
    echo "iniciando servicios de prueba..."
    if docker-compose -f docker-compose.simple.yml up -d; then
        success "servicios iniciados"
    else
        error "fallo al iniciar servicios"
        return 1
    fi
    
    # esperar a que servicios esten listos
    echo "esperando servicios..."
    sleep 30
    
    # ejecutar pruebas e2e
    echo "ejecutando pruebas e2e..."
    if python -m pytest tests/e2e/test_simple_e2e.py -v --tb=short; then
        success "pruebas e2e ok"
    else
        error "pruebas e2e fallaron"
        docker-compose -f docker-compose.simple.yml down
        return 1
    fi
    
    # limpiar
    docker-compose -f docker-compose.simple.yml down
    cd "$PROJECT_ROOT"
}

# verificar dependencias basicas
check_dependencies() {
    local missing=()
    
    command -v python &> /dev/null || missing+=("python")
    command -v terraform &> /dev/null || missing+=("terraform")
    command -v docker-compose &> /dev/null || missing+=("docker-compose")
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "dependencias faltantes: ${missing[*]}"
        echo "instala las dependencias requeridas"
        return 1
    fi
    
    success "dependencias ok"
}

# ejecutar pipeline
main() {
    echo "pipeline de verificacion simplificado"
    echo "===================================="
    
    check_dependencies || exit 1
    echo ""
    
    static_analysis || exit 1
    echo ""
    
    contract_tests || exit 1
    echo ""
    
    integration_tests || exit 1
    echo ""
    
    e2e_tests || exit 1
    echo ""
    
    success "pipeline completado exitosamente"
}

# permitir ejecutar fases individuales
case "${1:-all}" in
    "static")
        check_dependencies && static_analysis
        ;;
    "contract")
        check_dependencies && contract_tests
        ;;
    "integration")
        check_dependencies && integration_tests
        ;;
    "e2e")
        check_dependencies && e2e_tests
        ;;
    "all"|"")
        main
        ;;
    *)
        echo "uso: $0 [static|contract|integration|e2e|all]"
        echo "fases:"
        echo "  static      - analisis estatico de codigo"
        echo "  contract    - pruebas contractuales"
        echo "  integration - pruebas de integracion terraform"
        echo "  e2e         - pruebas end-to-end"
        echo "  all         - ejecutar todas las fases"
        exit 1
        ;;
esac 