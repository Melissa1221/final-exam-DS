"""
Factory parametrizable para crear recursos de compute que representan
nodos virtuales, contenedores y clusters de Kubernetes simulados.
"""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from enum import Enum

class ComputeType(Enum):
    """Tipos de recursos de compute disponibles."""
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container" 
    KUBERNETES_NODE = "kubernetes_node"
    KUBERNETES_MASTER = "kubernetes_master"
    

class ComputeFactory:
    """
    Factory parametrizable para crear diferentes tipos de recursos de compute.
    Implementa el patrón factory con parametrización para flexibilidad.
    """
    
    @staticmethod
    def create_virtual_machine(name: str, instance_type: str = "t3.medium",
                              subnet_name: str = None, 
                              tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea una máquina virtual simulada.
        """
        tags = tags or {}
        
        triggers = {
            "resource_type": ComputeType.VIRTUAL_MACHINE.value,
            "name": name,
            "instance_id": f"i-{uuid.uuid4().hex[:8]}",
            "instance_type": instance_type,
            "subnet_dependency": subnet_name or "default",
            "private_ip": f"10.0.{uuid.uuid4().bytes[0]}.{uuid.uuid4().bytes[1]}",
            "state": "running",
            "created_at": datetime.utcnow().isoformat(),
            "tags": str()
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"vm_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_container(name: str, image: str = "nginx:latest",
                        ports: List[int] = None,
                        environment: Dict[str, str] = None,
                        tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un contenedor simulado
        """
        tags = tags or {}
        ports = ports or [80]
        environment = environment or {}
        
        triggers = {
            "resource_type": ComputeType.CONTAINER.value,
            "name": name,
            "container_id": f"cnt-{uuid.uuid4().hex[:8]}",
            "image": image,
            "ports": str(ports),
            "environment": str(environment),
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
            "restart_policy": "always",
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"container_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_kubernetes_node(name: str, cluster_name: str, 
                              node_type: str = "worker",
                              instance_type: str = "t3.medium",
                              subnet_name: str = None,
                              tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un nodo de Kubernetes simulado.
        """
        tags = tags or {}
        
        # Determinar el tipo de recurso según el tipo de nodo
        resource_type = (ComputeType.KUBERNETES_MASTER.value 
                        if node_type == "master" 
                        else ComputeType.KUBERNETES_NODE.value)
        
        triggers = {
            "resource_type": resource_type,
            "name": name,
            "node_id": f"k8s-{uuid.uuid4().hex[:8]}",
            "cluster_dependency": cluster_name,
            "node_type": node_type,
            "instance_type": instance_type,
            "subnet_dependency": subnet_name or "default",
            "kubernetes_version": "1.28.0",
            "container_runtime": "containerd",
            "private_ip": f"10.0.{uuid.uuid4().bytes[0]}.{uuid.uuid4().bytes[1]}",
            "status": "Ready",
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"k8s_node_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class KubernetesClusterFactory:
    """
    Factory especializado para crear clusters completos de Kubernetes
    con múltiples nodos y configuraciones
    """
    
    @staticmethod
    def create_minikube_cluster(cluster_name: str, 
                               node_count: int = 3,
                               master_instance_type: str = "t3.medium",
                               worker_instance_type: str = "t3.medium",
                               subnet_configs: List[Dict[str, str]] = None,
                               tags: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Crea un cluster de Minikube simulado con nodos master y worker
        """
        tags = tags or {}
        subnet_configs = subnet_configs or [{"name": "default"}]
        resources = []
        
        # Crear nodo master
        master_node = ComputeFactory.create_kubernetes_node(
            name=f"{cluster_name}-master",
            cluster_name=cluster_name,
            node_type="master",
            instance_type=master_instance_type,
            subnet_name=subnet_configs[0]["name"],
            tags={**tags, "role": "master"}
        )
        resources.append(master_node)
        
        # Crear nodos worker distribuidos en las subredes disponibles
        for i in range(node_count):
            # Distribuir nodos en las subredes disponibles 
            subnet_config = subnet_configs[i % len(subnet_configs)]
            
            worker_node = ComputeFactory.create_kubernetes_node(
                name=f"{cluster_name}-worker-{i+1}",
                cluster_name=cluster_name,
                node_type="worker", 
                instance_type=worker_instance_type,
                subnet_name=subnet_config["name"],
                tags={**tags, "role": "worker", "worker_id": str(i+1)}
            )
            resources.append(worker_node)
        
        # Crear recurso de cluster 
        cluster_metadata = {
            "resource": [{
                "null_resource": [{
                    f"cluster_{cluster_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_cluster",
                            "cluster_name": cluster_name,
                            "cluster_id": f"cls-{uuid.uuid4().hex[:8]}",
                            "total_nodes": str(node_count + 1),  # +1 por el master
                            "master_count": "1",
                            "worker_count": str(node_count),
                            "kubernetes_version": "1.28.0",
                            "cluster_type": "minikube",
                            "created_at": datetime.utcnow().isoformat(),
                            "tags": str(tags)
                        }
                    }]
                }]
            }]
        }
        resources.append(cluster_metadata)
        
        return resources

class ParameterizedComputeFactory:
    """
    Factory parametrizable de alto nivel que permite crear 
    recursos de compute basados en configuraciones flexibles.
    """
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Crea recursos de compute basados en una configuración parametrizada.
        """
        resources = []
        compute_type = config.get("type", "virtual_machine")
        
        if compute_type == "kubernetes_cluster":
            cluster_resources = KubernetesClusterFactory.create_minikube_cluster(
                cluster_name=config["name"],
                node_count=config.get("node_count", 3),
                master_instance_type=config.get("master_instance_type", "t3.medium"),
                worker_instance_type=config.get("worker_instance_type", "t3.medium"),
                subnet_configs=config.get("subnet_configs", []),
                tags=config.get("tags", {})
            )
            resources.extend(cluster_resources)
            
        elif compute_type == "virtual_machine":
            vm_resource = ComputeFactory.create_virtual_machine(
                name=config["name"],
                instance_type=config.get("instance_type", "t3.medium"),
                subnet_name=config.get("subnet_name"),
                tags=config.get("tags", {})
            )
            resources.append(vm_resource)
            
        elif compute_type == "container":
            container_resource = ComputeFactory.create_container(
                name=config["name"],
                image=config.get("image", "nginx:latest"),
                ports=config.get("ports", [80]),
                environment=config.get("environment", {}),
                tags=config.get("tags", {})
            )
            resources.append(container_resource)
            
        return resources 