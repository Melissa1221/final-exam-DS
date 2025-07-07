# Examen final Desarrollo de Software

Problema 1
Se implementó la arquitectura de una red privada la cual contienen 2 subredes, internet gateway, route tables, implementado con kubernetes el cual maneja un cluster con 1 master y 3 workers, namespaces y aplicaciones. También roles específicos integrados
Las instrucciones son
```bash
python3 generate_infrastructure.py
```

### Desplegar con Terraform
```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

Problema 2
Se construye un pipeline local que implementa múltiples capas de verificación como análisis estático de código mediante tflint y terraform compliance. Incluye pruebas de integración y pruebas end-to-end

#### Instrucciones

```bash
# instalar dependencias python
pip install -r pipeline/requirements-simple.txt

# hacer ejecutable el pipeline
chmod +x pipeline/run_simple_pipeline.sh
```
verifica sintaxis y calidad del codigo terraform y python.

Ejecución
```bash
./pipeline/run_simple_pipeline.sh static
```
Pruebas contractuales:

valida contratos entre consumidores y productores de apis usando mocks.

Ejecución
```bash
./pipeline/run_simple_pipeline.sh contract
```
Pruebas de integración:

genera terraform plan en workspace aislado y valida outputs esperados.

Ejecución
```bash
./pipeline/run_simple_pipeline.sh integration
```
Pruebas E2E
simula ejecucion real de servicios con docker compose y verifica respuestas http.

Ejecución
```bash
./pipeline/run_simple_pipeline.sh e2e
```
Problema 3

Implementación de dos microservicios en python con docker multi-stage.

## servicios

- user-service: (puerto 8000): crear, listar, eliminar usuarios
- product-service: (puerto 8001): crear, buscar, actualizar productos

```bash
# Mover al directorio
cd microservices

# levantar servicios
docker-compose up -d

# publicar en registry local
chmod +x scripts/build-and-publish.sh
./scripts/build-and-publish.sh

# verificar funcionamiento
curl http://localhost:8000/health
curl http://localhost:8001/health

# endpoints principales
curl http://localhost:8000/users
curl http://localhost:8001/products
```

