#!/usr/bin/env python3
"""
Generador de infraestructura de red privada con kubernetes
"""

import os
import json
from typing import Dict, Any

from iac.singleton import ConfigSingleton
from iac.network_factory import NetworkModuleFactory
from iac.network_composite import NetworkModuleBuilder
from iac.compute_factory import ParameterizedComputeFactory
from iac.kubernetes_module import KubernetesModule
from iac.iam_module import IAMModule
from iac.dependency_injection import InfrastructureOrchestrator
from iac.composite import CompositeModule

class InfrastructureBuilder:
    """
    Builder principal que coordina toda la creación de infraestructura
    usando los patrones implementados y inyección de dependencias.
    """
    
    def __init__(self, project_name: str = "red-privada-k8s"):
        """
        Inicializa el builder de infraestructura
        """
        # Usar Singleton para configuración global
        self.config = ConfigSingleton(env_name="desarrollo-local")
        self.config.set("proyecto", project_name)
        self.config.set("region", "us-east-1")
        self.config.set("environment", "development")
        
        # Inicializar orquestador con inyección de dependencias
        self.orchestrator = InfrastructureOrchestrator(project_name)
        
        # Configuraciones por defecto
        self.network_config = {
            "vpc_name": f"{project_name}-vpc",
            "vpc_cidr": "10.0.0.0/16",
            "subnet_count": 2,
            "tags": {
                "Project": project_name,
                "Environment": self.config.get("environment"),
                "ManagedBy": "TerraformPatterns"
            }
        }
        
        self.kubernetes_config = {
            "cluster_name": f"{project_name}-cluster",
            "node_count": 3,
            "master_instance_type": "t3.medium",
            "worker_instance_type": "t3.medium"
        }
        
        # Módulo composite final para exportación
        self.final_module = CompositeModule()
    
    def build_network_infrastructure(self) -> "InfrastructureBuilder":
        """
        Construye la infraestructura de red usando el patrón composite y builder
        """
        print(f"Construyendo infraestructura de red para '{self.network_config['vpc_name']}'")
        
        # Usar NetworkModuleBuilder con patrón Builder
        network_builder = NetworkModuleBuilder(self.config.get("proyecto"))
        
        # Construir red privada con dos subredes
        self.network_infrastructure = network_builder.with_private_network(
            vpc_name=self.network_config["vpc_name"],
            subnet_count=self.network_config["subnet_count"],
            base_cidr=self.network_config["vpc_cidr"],
            tags=self.network_config["tags"]
        ).build()
        
        # Registrar en el orquestador para inyección de dependencias
        self.orchestrator.register_network_infrastructure(self.network_infrastructure)
        
        print(f"[Builder] Red privada creada con {self.network_config['subnet_count']} subredes")
        return self
    
    def build_kubernetes_cluster(self) -> "InfrastructureBuilder":
        """
        Construye el cluster de Kubernetes con dependencias inyectadas.
        """
        print(f"[Builder] Construyendo cluster Kubernetes '{self.kubernetes_config['cluster_name']}'")
        
        # Crear módulo Kubernetes
        self.k8s_module = KubernetesModule(self.config.get("proyecto"))
        
        # Inyectar dependencia de red (patrón de inyección de dependencias)
        self.k8s_module.inject_network_dependency(self.network_infrastructure)
        
        
        # Crear cluster con configuración
        self.k8s_module.create_cluster(
            cluster_name=self.kubernetes_config["cluster_name"],
            compute_config={
                "node_count": self.kubernetes_config["node_count"],
                "master_instance_type": self.kubernetes_config["master_instance_type"],
                "worker_instance_type": self.kubernetes_config["worker_instance_type"]
            },
            tags=self.network_config["tags"]
        )
        
        # Agregar namespaces comunes
        self.k8s_module.add_namespace("kube-system", {"managed-by": "terraform"})
        self.k8s_module.add_namespace("default", {"managed-by": "terraform"})
        self.k8s_module.add_namespace("monitoring", {"managed-by": "terraform"})
        
        # Agregar aplicaciones de ejemplo
        self.k8s_module.add_application(
            app_name="nginx-demo",
            namespace="default",
            image="nginx:1.21",
            replicas=2,
            ports=[80]
        )
        
        self.k8s_module.add_application(
            app_name="prometheus",
            namespace="monitoring", 
            image="prom/prometheus:latest",
            replicas=1,
            ports=[9090]
        )
        
        print(f"[Builder] Cluster Kubernetes creado con {self.kubernetes_config['node_count']} nodos worker")
        return self
    
    def build_additional_compute_resources(self) -> "InfrastructureBuilder":
        """
        Construye recursos adicionales de compute usando Factory parametrizable.
        """
        print("[Builder] Agregando recursos adicionales de compute")
        
        # Usar ParameterizedComputeFactory para recursos adicionales
        additional_resources = []
        
        # VM para bastion host
        bastion_config = {
            "type": "virtual_machine",
            "name": "bastion-host",
            "instance_type": "t3.micro",
            "subnet_name": f"{self.network_config['vpc_name']}_private_1",
            "tags": {**self.network_config["tags"], "Role": "BastionHost"}
        }
        bastion_resources = ParameterizedComputeFactory.create_from_config(bastion_config)
        additional_resources.extend(bastion_resources)
        
        # Contenedor para monitoring adicional
        monitoring_config = {
            "type": "container",
            "name": "grafana",
            "image": "grafana/grafana:latest",
            "ports": [3000],
            "environment": {"GF_SECURITY_ADMIN_PASSWORD": "admin123"},
            "tags": {**self.network_config["tags"], "Role": "Monitoring"}
        }
        monitoring_resources = ParameterizedComputeFactory.create_from_config(monitoring_config)
        additional_resources.extend(monitoring_resources)
        
        # Agregar recursos al módulo composite
        for resource in additional_resources:
            self.final_module.add(resource)
        
        print(f"[Builder] Agregados {len(additional_resources)} recursos adicionales de compute")
        return self
    
    def finalize_and_export(self, output_path: str = None) -> Dict[str, Any]:
        """
        Finaliza la construcción y exporta toda la infraestructura.
        """
        print("Finalizando y exportando infraestructura completa")
        
        # Orquestar toda la infraestructura usando inyección de dependencias prubas contractuales
        #implementa prubas tipo pact para endpoints simulados 
        complete_infrastructure = self.orchestrator.orchestrate()
        
        # Obtener recursos de cada componente
        network_resources = self.network_infrastructure.export_complete_infrastructure()
        k8s_resources = self.k8s_module.export_all_resources()
        
        # Combinar todos los recursos en el módulo composite final
        if "network_resources" in network_resources:
            for resource in network_resources["network_resources"]:
                self.final_module.add(resource)
        
        if "iam_resources" in network_resources:
            for resource in network_resources["iam_resources"]:
                self.final_module.add(resource)
        
        # Agregar recursos de Kubernetes
        for resource_type, resources in k8s_resources.items():
            if isinstance(resources, list):
                for resource in resources:
                    self.final_module.add(resource)
            elif isinstance(resources, dict) and "resource" in resources:
                self.final_module.add(resources)
        
        # Exportar módulo composite final
        final_terraform_config = self.final_module.export()
        
        # Preparar estructura final
        infrastructure_summary = {
            "project_config": {
                "name": self.config.get("proyecto"),
                "environment": self.config.get("environment"), 
                "region": self.config.get("region"),
                "created_with_patterns": [
                    "Singleton (ConfigSingleton)",
                    "Factory (NetworkFactory, ComputeFactory)", 
                    "Composite (NetworkComposite, CompositeModule)",
                    "Builder (NetworkModuleBuilder, InfrastructureBuilder)",
                    "Dependency Injection (InfrastructureOrchestrator)"
                ]
            },
            "network_summary": {
                "vpc_name": self.network_config["vpc_name"],
                "vpc_cidr": self.network_config["vpc_cidr"],
                "subnet_count": self.network_config["subnet_count"],
                "total_network_resources": len(network_resources.get("network_resources", []))
            },
            "kubernetes_summary": {
                "cluster_name": self.kubernetes_config["cluster_name"],
                "node_count": self.kubernetes_config["node_count"] + 1,  # +1 master
                "namespaces": len(k8s_resources.get("namespace_resources", [])),
                "applications": len(k8s_resources.get("application_resources", [])) // 2  # deployment + service
            },
            "dependency_analysis": complete_infrastructure.get("dependency_info", {}),
            "total_resources": len(final_terraform_config.get("resource", []))
        }
        
        # Exportar archivos si se especifica una ruta
        if output_path:
            self._export_terraform_files(final_terraform_config, infrastructure_summary, output_path)
        
        print(f"Infraestructura completa construida: {infrastructure_summary['total_resources']} recursos")
        print(f"Red: {infrastructure_summary['network_summary']['total_network_resources']} recursos")
        print(f"Kubernetes: {infrastructure_summary['kubernetes_summary']['node_count']} nodos")
        print(f"IAM: Roles y políticas integradas")
        
        return {
            "terraform_config": final_terraform_config,
            "infrastructure_summary": infrastructure_summary,
            "orchestration_details": complete_infrastructure
        }
    
    def _export_terraform_files(self, terraform_config: Dict[str, Any], 
                               summary: Dict[str, Any], output_path: str) -> None:
        """
        Exporta los archivos Terraform y documentación.
        
        """
        # Asegurar que el directorio existe
        os.makedirs(output_path, exist_ok=True)
        
        # Exportar configuración principal
        main_tf_path = os.path.join(output_path, "main.tf.json")
        with open(main_tf_path, "w") as f:
            json.dump(terraform_config, f, indent=2)
        
        # Exportar resumen como documentación
        summary_path = os.path.join(output_path, "infrastructure_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
    