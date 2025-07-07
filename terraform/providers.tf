terraform {
  required_version = ">= 1.5"
  
  required_providers {
    # Provider null para recursos de prueba y simulación
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    
    # Provider local para archivos y configuraciones locales
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    
    # Provider random para generar valores únicos
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    
    # Provider docker para simular contenedores
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Configuración del provider null
provider "null" {
  
}

# Configuración del provider local
provider "local" {
  
}

# Configuración del provider random
provider "random" {
  
}

# Configuración del provider docker 
provider "docker" {
  # Para uso local sin Docker daemon, se configurará según necesidades
} 