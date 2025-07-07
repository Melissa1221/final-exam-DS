"""
Factory especializado para crear recursos de red como VPC, subredes, 
gateways y tablas de enrutamiento en formato Terraform JSON.
"""

from typing import Dict, Any, List
import uuid
from datetime import datetime

class NetworkFactory:
    """
    Factory para crear recursos de red Terraform en formato JSON.
    Implementa el patrón factory para crear diferentes tipos de recursos de red.
    """
    
    @staticmethod
    def create_vpc(name: str, cidr_block: str, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un recurso VPC simulado usando null_resource con metadatos de red.
        """
        tags = tags or {}
        
        # Triggers que simulan la configuración de un VPC real
        triggers = {
            "resource_type": "vpc",
            "cidr_block": cidr_block,
            "name": name,
            "vpc_id": f"vpc-{uuid.uuid4().hex[:8]}",
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags),
            "enable_dns_hostnames": "true",
            "enable_dns_support": "true"
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"vpc_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod 
    def create_subnet(name: str, vpc_name: str, cidr_block: str, 
                     availability_zone: str = "us-east-1a", 
                     is_private: bool = True,
                     tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un recurso de subred simulado.
        """
        tags = tags or {}
        
        triggers = {
            "resource_type": "subnet",
            "name": name,
            "subnet_id": f"subnet-{uuid.uuid4().hex[:8]}",
            "vpc_dependency": vpc_name,  # Simula dependencia
            "cidr_block": cidr_block,
            "availability_zone": availability_zone,
            "is_private": str(is_private),
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"subnet_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_internet_gateway(name: str, vpc_name: str, 
                               tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un Internet Gateway simulado.
        """
        tags = tags or {}
        
        triggers = {
            "resource_type": "internet_gateway",
            "name": name,
            "igw_id": f"igw-{uuid.uuid4().hex[:8]}",
            "vpc_dependency": vpc_name,
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"igw_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_route_table(name: str, vpc_name: str, routes: List[Dict[str, str]] = None,
                          tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea una tabla de enrutamiento simulada.
        """
        tags = tags or {}
        routes = routes or []
        
        triggers = {
            "resource_type": "route_table",
            "name": name,
            "rt_id": f"rtb-{uuid.uuid4().hex[:8]}",
            "vpc_dependency": vpc_name,
            "routes": str(routes),
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"route_table_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class NetworkModuleFactory:
    """
    Factory de alto nivel que crea módulos completos de red
    usando composición de recursos básicos.
    """
    
    @staticmethod
    def create_private_network_module(vpc_name: str, vpc_cidr: str, 
                                    subnet_configs: List[Dict[str, str]],
                                    tags: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Crea un módulo completo de red privada con VPC y múltiples subredes.
        """
        tags = tags or {}
        resources = []
        
        # Crear VPC
        vpc_resource = NetworkFactory.create_vpc(vpc_name, vpc_cidr, tags)
        resources.append(vpc_resource)
        
        # Crear Internet Gateway
        igw_resource = NetworkFactory.create_internet_gateway(f"{vpc_name}_igw", vpc_name, tags)
        resources.append(igw_resource)
        
        # Crear subredes según configuración
        for subnet_config in subnet_configs:
            subnet_resource = NetworkFactory.create_subnet(
                name=subnet_config["name"],
                vpc_name=vpc_name,
                cidr_block=subnet_config["cidr"],
                availability_zone=subnet_config.get("zone", "us-east-1a"),
                is_private=subnet_config.get("is_private", True),
                tags=tags
            )
            resources.append(subnet_resource)
        
        # Crear tabla de rutas para subredes privadas
        route_table_resource = NetworkFactory.create_route_table(
            f"{vpc_name}_private_rt", 
            vpc_name,
            tags=tags
        )
        resources.append(route_table_resource)
        
        return resources 