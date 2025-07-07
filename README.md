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
construye un pipeline local que imlemente multiples capas de verificacion
analisis estatico de codigo mediante tflint y terraform compliance asegura el cumplimiento de buenas prácticas y politicas de infraestructura simulada
pruebas contractuales
