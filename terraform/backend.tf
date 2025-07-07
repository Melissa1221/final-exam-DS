# Configuración del backend local para almacenar el estado de Terraform
# Implementa el patrón Singleton para el estado compartido

terraform {
  backend "local" {
    # Ruta donde se almacenará el archivo de estado
    path = "./terraform.tfstate"
    
    # Configuración para evitar conflictos en escritura concurrente
    workspace_dir = "./workspace"
  }
}

# Variables de configuración del backend (patrón de configuración centralizada)
locals {
  backend_config = {
    state_file_path = "./terraform.tfstate"
    backup_enabled  = true
    backup_path     = "./terraform.tfstate.backup"
    
    # Metadatos del proyecto
    project_name = "red-privada-k8s"
    environment  = "desarrollo-local"
    version      = "1.0.0"
    
    # Configuración de red
    network_config = {
      vpc_cidr = "10.0.0.0/16"
      subnet_configs = [
        {
          name = "subnet-private-1"
          cidr = "10.0.1.0/24"
          zone = "us-east-1a"
        },
        {
          name = "subnet-private-2" 
          cidr = "10.0.2.0/24"
          zone = "us-east-1b"
        }
      ]
    }
    
    # Configuración del cluster Kubernetes
    k8s_config = {
      cluster_name = "minikube-cluster"
      node_count   = 3
      node_type    = "t3.medium"
    }
  }
} 