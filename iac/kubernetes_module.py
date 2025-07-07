"""
Módulo para crear clusters de Kubernetes simulados usando minikube
con dependencias en módulos de red y compute.
"""

from typing import Dict, Any, List, Optional
from .compute_factory import KubernetesClusterFactory, ParameterizedComputeFactory
from .network_composite import NetworkInfrastructureComposite
from .iam_module import IAMModule
import uuid
from datetime import datetime

class KubernetesComponent:
    """
    Componente base para recursos de Kubernetes.
    Implementa interfaz común para diferentes tipos de recursos K8s.
    """
    
    def export(self) -> List[Dict[str, Any]]:
        """
        Exporta los recursos del componente.
        """
        raise NotImplementedError("Subclases deben implementar export()")
    
    def get_dependencies(self) -> List[str]:
        """
        Obtiene las dependencias del componente.
        """
        return []

class MinikubeCluster(KubernetesComponent):
    """
    Representa un cluster de Minikube simulado con todas sus dependencias.
    """
    
    def __init__(self, cluster_name: str, network_config: Dict[str, Any], 
                 compute_config: Dict[str, Any] = None, 
                 tags: Dict[str, str] = None):
        """
        Inicializa un cluster de Minikube.
        """
        self.cluster_name = cluster_name
        self.network_config = network_config
        self.compute_config = compute_config or {}
        self.tags = tags or {}
        
        # Configuración por defecto para compute
        self.compute_config.setdefault("node_count", 3)
        self.compute_config.setdefault("master_instance_type", "t3.medium")
        self.compute_config.setdefault("worker_instance_type", "t3.medium")
        
        # Generar recursos del cluster
        self.cluster_resources = self._create_cluster_resources()
        self.addons_resources = self._create_addon_resources()
    
    def _create_cluster_resources(self) -> List[Dict[str, Any]]:
        """
        Crea los recursos principales del cluster.
        """
        # Obtener configuración de subredes desde la red
        subnet_configs = []
        for subnet_name in self.network_config.get("subnet_names", []):
            subnet_configs.append({"name": subnet_name})
        
        # Crear cluster usando el factory
        cluster_resources = KubernetesClusterFactory.create_minikube_cluster(
            cluster_name=self.cluster_name,
            node_count=self.compute_config["node_count"],
            master_instance_type=self.compute_config["master_instance_type"],
            worker_instance_type=self.compute_config["worker_instance_type"],
            subnet_configs=subnet_configs,
            tags=self.tags
        )
        
        return cluster_resources
    
    def _create_addon_resources(self) -> List[Dict[str, Any]]:
        """
        Crea recursos adicionales para el cluster (addons simulados).
        """
        addons = []
        
        # DNS addon
        dns_addon = {
            "resource": [{
                "null_resource": [{
                    f"k8s_addon_dns_{self.cluster_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_addon",
                            "addon_name": "coredns",
                            "cluster_dependency": self.cluster_name,
                            "addon_version": "1.10.1",
                            "enabled": "true",
                            "replicas": "2",
                            "created_at": datetime.utcnow().isoformat(),
                            "tags": str(self.tags)
                        }
                    }]
                }]
            }]
        }
        addons.append(dns_addon)
        
        # Ingress Controller addon
        ingress_addon = {
            "resource": [{
                "null_resource": [{
                    f"k8s_addon_ingress_{self.cluster_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_addon",
                            "addon_name": "nginx-ingress",
                            "cluster_dependency": self.cluster_name,
                            "addon_version": "1.8.1",
                            "enabled": "true",
                            "service_type": "LoadBalancer",
                            "created_at": datetime.utcnow().isoformat(),
                            "tags": str(self.tags)
                        }
                    }]
                }]
            }]
        }
        addons.append(ingress_addon)
        
        # Metrics Server addon
        metrics_addon = {
            "resource": [{
                "null_resource": [{
                    f"k8s_addon_metrics_{self.cluster_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_addon",
                            "addon_name": "metrics-server",
                            "cluster_dependency": self.cluster_name,
                            "addon_version": "0.6.4",
                            "enabled": "true",
                            "created_at": datetime.utcnow().isoformat(),
                            "tags": str(self.tags)
                        }
                    }]
                }]
            }]
        }
        addons.append(metrics_addon)
        
        return addons
    
    def export(self) -> List[Dict[str, Any]]:
        """
        Exporta todos los recursos del cluster.
        """
        all_resources = []
        all_resources.extend(self.cluster_resources)
        all_resources.extend(self.addons_resources)
        return all_resources
    
    def get_dependencies(self) -> List[str]:
        """
        Obtiene las dependencias del cluster.
        """
        dependencies = []
        dependencies.append(self.network_config.get("vpc_name", ""))
        dependencies.extend(self.network_config.get("subnet_names", []))
        return [dep for dep in dependencies if dep]  # Filtrar cadenas vacías

class KubernetesNamespace:
    """
    Representa un namespace de Kubernetes simulado.
    """
    
    def __init__(self, namespace_name: str, cluster_name: str, 
                 labels: Dict[str, str] = None,
                 annotations: Dict[str, str] = None):
        """
        Inicializa un namespace.
        """
        self.namespace_name = namespace_name
        self.cluster_name = cluster_name
        self.labels = labels or {}
        self.annotations = annotations or {}
    
    def export(self) -> Dict[str, Any]:
        """
        Exporta el recurso del namespace.
        """
        triggers = {
            "resource_type": "kubernetes_namespace",
            "namespace_name": self.namespace_name,
            "cluster_dependency": self.cluster_name,
            "labels": str(self.labels),
            "annotations": str(self.annotations),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"k8s_namespace_{self.namespace_name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class KubernetesApplication:
    """
    Representa una aplicación desplegada en Kubernetes.
    """
    
    def __init__(self, app_name: str, namespace: str, cluster_name: str,
                 image: str = "nginx:latest", replicas: int = 2,
                 ports: List[int] = None, environment: Dict[str, str] = None):
        """
        Inicializa una aplicación.
        """
        self.app_name = app_name
        self.namespace = namespace
        self.cluster_name = cluster_name
        self.image = image
        self.replicas = replicas
        self.ports = ports or [80]
        self.environment = environment or {}
    
    def export(self) -> List[Dict[str, Any]]:
        """
        Exporta los recursos de la aplicación (Deployment y Service).
        """
        resources = []
        
        # Deployment
        deployment = {
            "resource": [{
                "null_resource": [{
                    f"k8s_deployment_{self.app_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_deployment",
                            "app_name": self.app_name,
                            "namespace_dependency": self.namespace,
                            "cluster_dependency": self.cluster_name,
                            "image": self.image,
                            "replicas": str(self.replicas),
                            "ports": str(self.ports),
                            "environment": str(self.environment),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    }]
                }]
            }]
        }
        resources.append(deployment)
        
        # Service
        service = {
            "resource": [{
                "null_resource": [{
                    f"k8s_service_{self.app_name}": [{
                        "triggers": {
                            "resource_type": "kubernetes_service",
                            "service_name": f"{self.app_name}-service",
                            "app_dependency": self.app_name,
                            "namespace_dependency": self.namespace,
                            "cluster_dependency": self.cluster_name,
                            "service_type": "ClusterIP",
                            "ports": str(self.ports),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    }]
                }]
            }]
        }
        resources.append(service)
        
        return resources

class KubernetesModule:
    """
    Módulo composite que agrupa cluster, namespaces, aplicaciones e IAM.
    Implementa inyección de dependencias con módulos de red.
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa el módulo Kubernetes.
        """
        self.module_name = module_name
        self.cluster: Optional[MinikubeCluster] = None
        self.namespaces: List[KubernetesNamespace] = []
        self.applications: List[KubernetesApplication] = []
        self.iam_module: IAMModule = IAMModule(f"{module_name}_k8s_iam")
        self.network_dependency: Optional[NetworkInfrastructureComposite] = None
    
    def inject_network_dependency(self, network_infrastructure: NetworkInfrastructureComposite) -> "KubernetesModule":
        """
        Inyecta la dependencia de infraestructura de red.
        Implementa el patrón de inyección de dependencias.
        """
        self.network_dependency = network_infrastructure
        return self
    
    def create_cluster(self, cluster_name: str, compute_config: Dict[str, Any] = None,
                      tags: Dict[str, str] = None) -> "KubernetesModule":
        """
        Crea el cluster principal usando la dependencia de red inyectada.
        """
        if not self.network_dependency:
            raise ValueError("Debe inyectar dependencia de red antes de crear el cluster")
        
        # Extraer configuración de red desde la dependencia
        network_config = {
            "vpc_name": list(self.network_dependency.vpcs.keys())[0] if self.network_dependency.vpcs else "default",
            "subnet_names": [f"{vpc_name}_private_1" for vpc_name in self.network_dependency.vpcs.keys()] + 
                           [f"{vpc_name}_private_2" for vpc_name in self.network_dependency.vpcs.keys()]
        }
        
        # Crear cluster
        self.cluster = MinikubeCluster(cluster_name, network_config, compute_config, tags)
        
        # Agregar IAM para el cluster
        self.iam_module.add_kubernetes_rbac(cluster_name, tags)
        
        return self
    
    def add_namespace(self, namespace_name: str, labels: Dict[str, str] = None,
                     annotations: Dict[str, str] = None) -> "KubernetesModule":
        """
        Agrega un namespace al cluster.
        """
        if not self.cluster:
            raise ValueError("Debe crear un cluster antes de agregar namespaces")
        
        namespace = KubernetesNamespace(
            namespace_name, self.cluster.cluster_name, labels, annotations
        )
        self.namespaces.append(namespace)
        return self
    
    def add_application(self, app_name: str, namespace: str, 
                       image: str = "nginx:latest", replicas: int = 2,
                       ports: List[int] = None, 
                       environment: Dict[str, str] = None) -> "KubernetesModule":
        """
        Agrega una aplicación al cluster.
        """
        if not self.cluster:
            raise ValueError("Debe crear un cluster antes de agregar aplicaciones")
        
        application = KubernetesApplication(
            app_name, namespace, self.cluster.cluster_name, 
            image, replicas, ports, environment
        )
        self.applications.append(application)
        return self
    
    def export_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Exporta todos los recursos del módulo.
        """
        result = {
            "cluster_resources": [],
            "namespace_resources": [],
            "application_resources": [],
            "iam_resources": []
        }
        
        if self.cluster:
            result["cluster_resources"] = self.cluster.export()
        
        for namespace in self.namespaces:
            result["namespace_resources"].append(namespace.export())
        
        for application in self.applications:
            result["application_resources"].extend(application.export())
        
        result["iam_resources"] = self.iam_module.export_resources()
        
        return result
    
    def get_all_dependencies(self) -> List[str]:
        """
        Obtiene todas las dependencias del módulo.
        """
        dependencies = []
        
        if self.cluster:
            dependencies.extend(self.cluster.get_dependencies())
        
        return list(set(dependencies))  # Remover duplicados 