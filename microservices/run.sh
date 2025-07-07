#!/bin/bash

set -e

echo "iniciando microservicios..."

# hacer ejecutables los scripts
chmod +x scripts/*.sh

# levantar servicios
docker-compose up -d

echo "servicios iniciados"
echo "user service: http://localhost:8000"
echo "product service: http://localhost:8001"
echo ""
echo "para publicar en registry local:"
echo "./scripts/build-and-publish.sh" 