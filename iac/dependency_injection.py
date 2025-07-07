"""
Implementa un sistema de inyección de dependencias para gestionar
las relaciones entre módulos de infraestructura.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic, Protocol
from abc import ABC, abstractmethod
import uuid
from datetime import datetime


T = TypeVar('T')

class Injectable(Protocol):
    """
    Protocolo que define los objetos que pueden ser inyectados.
    """
    
    def get_dependencies(self) -> List[str]:
        """Obtiene las dependencias del objeto."""
        ...
    
    def export(self) -> Any:
        """Exporta el contenido del objeto."""
        ...

class DependencyProvider(ABC):
    """
    Proveedor abstracto de dependencias.
    Define la interfaz para todos los proveedores.
    """
    
    @abstractmethod
    def provide(self) -> Injectable:
        """
        Provee una instancia del recurso gestionado.
        """
        pass
    
    @abstractmethod
    def get_type_name(self) -> str:
        """
        Obtiene el nombre del tipo que este proveedor maneja.
        """
        pass

class NetworkProvider(DependencyProvider):
    """
    Proveedor de dependencias para infraestructura de red.
    """
    
    def __init__(self, network_infrastructure):
        """
        Inicializa el proveedor de red.
        """
        self._network_infrastructure = network_infrastructure
    
    def provide(self) -> Injectable:
        """
        Provee la infraestructura de red.
        """
        return self._network_infrastructure
    
    def get_type_name(self) -> str:
        """
        Obtiene el nombre del tipo.
        """
        return "NetworkInfrastructure"

class ComputeProvider(DependencyProvider):
    """
    Proveedor de dependencias para recursos de compute.
    """
    
    def __init__(self, compute_factory):
        """
        Inicializa el proveedor de compute.
        """
        self._compute_factory = compute_factory
    
    def provide(self) -> Injectable:
        """
        Provee el factory de compute.
        """
        return self._compute_factory
    
    def get_type_name(self) -> str:
        return "ComputeFactory"

class IAMProvider(DependencyProvider):
    """
    Proveedor de dependencias para recursos IAM.
    """
    
    def __init__(self, iam_module):
        """
        Inicializa el proveedor IAM.
        """
        self._iam_module = iam_module
    
    def provide(self) -> Injectable:
        """
        Provee el módulo IAM.
        """
        return self._iam_module
    
    def get_type_name(self) -> str:
        """
        Obtiene el nombre del tipo.
        """
        return "IAMModule"

class DependencyContainer:
    """
    Contenedor de dependencias que gestiona el registro y resolución
    de dependencias entre módulos.
    """
    
    def __init__(self, container_name: str = "default"):
        """
        Inicializa el contenedor.
        """
        self.container_name = container_name
        self.container_id = f"dic-{uuid.uuid4().hex[:8]}"
        self.providers: Dict[str, DependencyProvider] = {}
        self.singletons: Dict[str, Injectable] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.resolution_order: List[str] = []
        self.created_at = datetime.utcnow().isoformat()
    
    def register_provider(self, provider: DependencyProvider, 
                         dependencies: List[str] = None) -> "DependencyContainer":
        """
        Registra un proveedor de dependencias.
        """
        type_name = provider.get_type_name()
        self.providers[type_name] = provider
        self.dependency_graph[type_name] = dependencies or []
        
        # Recalcular orden de resolución
        self._calculate_resolution_order()
        
        return self
    
    def register_singleton(self, type_name: str, instance: Injectable) -> "DependencyContainer":
        """
        Registra una instancia singleton.
        """
        self.singletons[type_name] = instance
        return self
    
    def resolve(self, type_name: str) -> Injectable:
        """
        Resuelve una dependencia por su nombre de tipo.
        """
        # Verificar si existe como singleton
        if type_name in self.singletons:
            return self.singletons[type_name]
        
        # Verificar si existe un proveedor
        if type_name not in self.providers:
            raise ValueError(f"Tipo '{type_name}' no está registrado en el contenedor")
        
        # Resolver dependencias primero
        for dependency_type in self.dependency_graph.get(type_name, []):
            if dependency_type not in self.singletons:
                self.singletons[dependency_type] = self.resolve(dependency_type)
        
        # Crear instancia usando el proveedor
        provider = self.providers[type_name]
        instance = provider.provide()
        
        # Guardar como singleton para futuras resoluciones
        self.singletons[type_name] = instance
        
        return instance
    
    def resolve_all(self) -> Dict[str, Injectable]:
        """
        Resuelve todas las dependencias registradas en orden.
        """
        resolved = {}
        
        for type_name in self.resolution_order:
            resolved[type_name] = self.resolve(type_name)
        
        return resolved
    
    def _calculate_resolution_order(self) -> None:
        """
        Calcula el orden de resolución de dependencias usando ordenamiento topológico.
        """
        # Implementación simple de ordenamiento topológico
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node: str):
            if node in temp_visited:
                raise ValueError(f"Dependencia circular detectada con '{node}'")
            
            if node not in visited:
                temp_visited.add(node)
                
                for dependency in self.dependency_graph.get(node, []):
                    if dependency in self.dependency_graph:
                        visit(dependency)
                
                temp_visited.remove(node)
                visited.add(node)
                order.append(node)
        
        for type_name in self.dependency_graph:
            if type_name not in visited:
                visit(type_name)
        
        self.resolution_order = order
    
    def get_dependency_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre las dependencias registradas.
        """
        return {
            "container_name": self.container_name,
            "container_id": self.container_id,
            "created_at": self.created_at,
            "registered_types": list(self.providers.keys()),
            "singletons": list(self.singletons.keys()),
            "dependency_graph": self.dependency_graph,
            "resolution_order": self.resolution_order,
            "total_providers": len(self.providers),
            "total_singletons": len(self.singletons)
        }

class InfrastructureOrchestrator:
    """
    Orquestador principal que coordina la creación de toda la infraestructura
    usando inyección de dependencias.
    """
    
    def __init__(self, orchestrator_name: str):
        """
        Inicializa el orquestador.
        """
        self.orchestrator_name = orchestrator_name
        self.orchestrator_id = f"orc-{uuid.uuid4().hex[:8]}"
        self.container = DependencyContainer(f"{orchestrator_name}_container")
        self.resolved_infrastructure: Dict[str, Injectable] = {}
        self.created_at = datetime.utcnow().isoformat()
    
    def register_network_infrastructure(self, network_infrastructure) -> "InfrastructureOrchestrator":
        """
        Registra la infraestructura de red.
        """
        provider = NetworkProvider(network_infrastructure)
        self.container.register_provider(provider, dependencies=[])
        return self
    
    def register_compute_resources(self, compute_factory, 
                                  depends_on_network: bool = True) -> "InfrastructureOrchestrator":
        """
        Registra recursos de compute.
        """
        dependencies = ["NetworkInfrastructure"] if depends_on_network else []
        provider = ComputeProvider(compute_factory)
        self.container.register_provider(provider, dependencies=dependencies)
        return self
    
    def register_iam_resources(self, iam_module, 
                              depends_on: List[str] = None) -> "InfrastructureOrchestrator":
        """
        Registra recursos IAM.
        """
        dependencies = depends_on or ["NetworkInfrastructure"]
        provider = IAMProvider(iam_module)
        self.container.register_provider(provider, dependencies=dependencies)
        return self
    
    def orchestrate(self) -> Dict[str, Any]:
        """
        Orquesta la creación de toda la infraestructura.
        """
        # Resolver todas las dependencias
        self.resolved_infrastructure = self.container.resolve_all()
        
        # Exportar recursos de cada componente
        infrastructure_resources = {}
        
        for component_type, component_instance in self.resolved_infrastructure.items():
            try:
                if hasattr(component_instance, 'export_complete_infrastructure'):
                    infrastructure_resources[component_type] = component_instance.export_complete_infrastructure()
                elif hasattr(component_instance, 'export_all_resources'):
                    infrastructure_resources[component_type] = component_instance.export_all_resources()
                elif hasattr(component_instance, 'export_resources'):
                    infrastructure_resources[component_type] = component_instance.export_resources()
                elif hasattr(component_instance, 'export'):
                    infrastructure_resources[component_type] = component_instance.export()
                else:
                    infrastructure_resources[component_type] = str(component_instance)
            except Exception as e:
                infrastructure_resources[component_type] = f"Error exporting: {str(e)}"
        
        return {
            "orchestrator_info": {
                "name": self.orchestrator_name,
                "id": self.orchestrator_id,
                "created_at": self.created_at
            },
            "dependency_info": self.container.get_dependency_info(),
            "infrastructure_resources": infrastructure_resources,
            "total_components": len(self.resolved_infrastructure)
        }
    
    def get_component(self, component_type: str) -> Optional[Injectable]:
        """
        Obtiene un componente específico ya resuelto.
        """
        return self.resolved_infrastructure.get(component_type)
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """
        Valida que todas las dependencias estén correctamente configuradas.
        """
        validation_report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "dependency_analysis": {}
        }
        
        try:
            # Verificar que se puede calcular el orden de resolución
            self.container._calculate_resolution_order()
            
            # Verificar cada dependencia
            for type_name, dependencies in self.container.dependency_graph.items():
                analysis = {
                    "has_provider": type_name in self.container.providers,
                    "dependencies_satisfied": []
                }
                
                for dep in dependencies:
                    dep_satisfied = (dep in self.container.providers or 
                                   dep in self.container.singletons)
                    analysis["dependencies_satisfied"].append({
                        "dependency": dep,
                        "satisfied": dep_satisfied
                    })
                    
                    if not dep_satisfied:
                        validation_report["errors"].append(
                            f"Dependencia '{dep}' de '{type_name}' no está registrada"
                        )
                        validation_report["is_valid"] = False
                
                validation_report["dependency_analysis"][type_name] = analysis
                
        except ValueError as e:
            validation_report["errors"].append(str(e))
            validation_report["is_valid"] = False
        
        return validation_report 