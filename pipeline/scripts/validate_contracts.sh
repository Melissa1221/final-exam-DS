#!/bin/bash

# script para validar contratos pact g

set -e

CONTRACTS_DIR="./pacts"
LOG_FILE="./test-results/contract-validation.log"

# colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# crear directorio de resultados si no existe
mkdir -p "$(dirname "$LOG_FILE")"

# verificar que existe directorio de contratos
if [ ! -d "$CONTRACTS_DIR" ]; then
    log_error "directorio de contratos no existe: $CONTRACTS_DIR"
    exit 1
fi

# buscar archivos de contrato
contract_files=$(find "$CONTRACTS_DIR" -name "*.json" -type f)

if [ -z "$contract_files" ]; then
    log_error "no se encontraron archivos de contrato en $CONTRACTS_DIR"
    exit 1
fi

log_info "iniciando validacion de contratos..."

# validar cada archivo de contrato
validation_passed=true

for contract_file in $contract_files; do
    log_info "validando: $(basename "$contract_file")"
    
    # verificar que es json valido
    if ! jq empty "$contract_file" 2>/dev/null; then
        log_error "archivo no es json valido: $contract_file"
        validation_passed=false
        continue
    fi
    
    # verificar estructura basica de pact
    consumer=$(jq -r '.consumer.name' "$contract_file" 2>/dev/null)
    provider=$(jq -r '.provider.name' "$contract_file" 2>/dev/null)
    interactions=$(jq '.interactions | length' "$contract_file" 2>/dev/null)
    
    if [ "$consumer" = "null" ] || [ "$consumer" = "" ]; then
        log_error "contrato sin consumer valido: $contract_file"
        validation_passed=false
        continue
    fi
    
    if [ "$provider" = "null" ] || [ "$provider" = "" ]; then
        log_error "contrato sin provider valido: $contract_file"
        validation_passed=false
        continue
    fi
    
    if [ "$interactions" = "null" ] || [ "$interactions" -eq 0 ]; then
        log_error "contrato sin interactions: $contract_file"
        validation_passed=false
        continue
    fi
    
    # verificar que cada interaction tiene los campos requeridos
    invalid_interactions=0
    for i in $(seq 0 $((interactions - 1))); do
        description=$(jq -r ".interactions[$i].description" "$contract_file" 2>/dev/null)
        request_method=$(jq -r ".interactions[$i].request.method" "$contract_file" 2>/dev/null)
        request_path=$(jq -r ".interactions[$i].request.path" "$contract_file" 2>/dev/null)
        response_status=$(jq -r ".interactions[$i].response.status" "$contract_file" 2>/dev/null)
        
        if [ "$description" = "null" ] || [ "$description" = "" ]; then
            log_warn "interaction $i sin description en $contract_file"
            invalid_interactions=$((invalid_interactions + 1))
        fi
        
        if [ "$request_method" = "null" ] || [ "$request_method" = "" ]; then
            log_error "interaction $i sin method en $contract_file"
            invalid_interactions=$((invalid_interactions + 1))
        fi
        
        if [ "$request_path" = "null" ] || [ "$request_path" = "" ]; then
            log_error "interaction $i sin path en $contract_file"
            invalid_interactions=$((invalid_interactions + 1))
        fi
        
        if [ "$response_status" = "null" ] || [ "$response_status" = "" ]; then
            log_error "interaction $i sin status en $contract_file"
            invalid_interactions=$((invalid_interactions + 1))
        fi
    done
    
    if [ $invalid_interactions -gt 0 ]; then
        log_error "$invalid_interactions interactions invalidas en $contract_file"
        validation_passed=false
    else
        log_info "contrato valido: $consumer -> $provider ($interactions interactions)"
    fi
done

# resumen final
if [ "$validation_passed" = true ]; then
    log_info "validacion de contratos completada exitosamente"
    exit 0
else
    log_error "validacion de contratos fallo"
    exit 1
fi 