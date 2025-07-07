from typing import Dict, Any, List
from .composite import CompositeModule
from .network_factory import NetworkFactory, NetworkModuleFactory
from .iam_module import IAMModule

class NetworkComponent:
    """
    Interfaz base para componentes de red.
    Implementa el patrón Composite para tratamiento uniforme.
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

class NetworkLeaf(NetworkComponent):
    """
    Hoja en el patrón Composite - representa un recurso individual de red.
    """
    
    def __init__(self, resource: Dict[str, Any], dependencies: List[str] = None):
        """
        Inicializa una hoja de red.
        """
        self.resource = resource
        self.dependencies = dependencies or []
    
    def export(self) -> List[Dict[str, Any]]:
        """
        Exporta el recurso individual.
        """
        return [self.resource]
    
    def get_dependencies(self) -> List[str]:
        """
        Obtiene las dependencias del recurso.
        """
        return self.dependencies.copy()

class NetworkComposite(NetworkComponent):
    """
    Composite en el patrón Composite - representa un conjunto de componentes de red.
    Puede contener tanto hojas como otros composites.
    """
    
    def __init__(self, name: str):
        """
        Inicializa un composite de red.
        """
        self.name = name
        self.children: List[NetworkComponent] = []
    
    def add(self, component: NetworkComponent) -> "NetworkComposite":
        """
        Agrega un componente hijo.
        """
        self.children.append(component)
        return self
    
    def remove(self, component: NetworkComponent) -> "NetworkComposite":
        """
        Remueve un componente hijo.
        """
        if component in self.children:
            self.children.remove(component)
        return self
    
    def export(self) -> List[Dict[str, Any]]:
        """
        Exporta todos los recursos de los componentes hijos.
        """
        resources = []
        for child in self.children:
            resources.extend(child.export())
        return resources
    
    def get_dependencies(self) -> List[str]:
        """
        Obtiene todas las dependencias de los componentes hijos.
        """
        dependencies = []
        for child in self.children:
            dependencies.extend(child.get_dependencies())
        return list(set(dependencies))  # Remover duplicados

class VPCComposite(NetworkComposite):
    """
    Composite especializado para VPCs que incluye factory methods
    para crear configuraciones comunes.
    """
    
    def __init__(self, vpc_name: str, vpc_cidr: str, tags: Dict[str, str] = None):
        """
        Inicializa un VPC composite.
        """
        super().__init__(f"vpc_{vpc_name}")
        self.vpc_name = vpc_name
        self.vpc_cidr = vpc_cidr
        self.tags = tags or {}
        
        # Crear VPC base
        vpc_resource = NetworkFactory.create_vpc(vpc_name, vpc_cidr, self.tags)
        self.vpc_leaf = NetworkLeaf(vpc_resource)
        self.add(self.vpc_leaf)
    
    def add_private_subnet(self, subnet_name: str, cidr: str, 
                          az: str = "us-east-1a") -> "VPCComposite":
        """
        Agrega una subred privada al VPC.
        """
        subnet_resource = NetworkFactory.create_subnet(
            subnet_name, self.vpc_name, cidr, az, True, self.tags
        )
        subnet_leaf = NetworkLeaf(subnet_resource, [self.vpc_name])
        self.add(subnet_leaf)
        return self
    
    def add_public_subnet(self, subnet_name: str, cidr: str,
                         az: str = "us-east-1a") -> "VPCComposite":
        """
        Agrega una subred pública al VPC.
        """
        subnet_resource = NetworkFactory.create_subnet(
            subnet_name, self.vpc_name, cidr, az, False, self.tags
        )
        subnet_leaf = NetworkLeaf(subnet_resource, [self.vpc_name])
        self.add(subnet_leaf)
        return self
    
    def add_internet_gateway(self) -> "VPCComposite":
        """
        Agrega un Internet Gateway al VPC.
        """
        igw_resource = NetworkFactory.create_internet_gateway(
            f"{self.vpc_name}_igw", self.vpc_name, self.tags
        )
        igw_leaf = NetworkLeaf(igw_resource, [self.vpc_name])
        self.add(igw_leaf)
        return self
    
    def add_route_table(self, rt_name: str, routes: List[Dict[str, str]] = None) -> "VPCComposite":
        """
        Agrega una tabla de rutas al VPC.
        """
        rt_resource = NetworkFactory.create_route_table(
            rt_name, self.vpc_name, routes, self.tags
        )
        rt_leaf = NetworkLeaf(rt_resource, [self.vpc_name])
        self.add(rt_leaf)
        return self

class NetworkInfrastructureComposite(NetworkComposite):
    """
    Composite de nivel superior que agrupa múltiples VPCs
    y otros componentes de infraestructura de red.
    """
    
    def __init__(self, infrastructure_name: str):
        """
        Inicializa la infraestructura de red composite.
        """
        super().__init__(f"network_infrastructure_{infrastructure_name}")
        self.infrastructure_name = infrastructure_name
        self.vpcs: Dict[str, VPCComposite] = {}
        self.iam_module: IAMModule = IAMModule(f"{infrastructure_name}_network_iam")
    
    def add_vpc(self, vpc_name: str, vpc_cidr: str, 
                tags: Dict[str, str] = None) -> VPCComposite:
        """
        Agrega un VPC a la infraestructura.
        """
        vpc_composite = VPCComposite(vpc_name, vpc_cidr, tags)
        self.vpcs[vpc_name] = vpc_composite
        self.add(vpc_composite)
        
        # Agregar RBAC para el VPC
        self.iam_module.add_network_rbac(vpc_name, tags)
        
        return vpc_composite
    
    def create_two_subnet_architecture(self, vpc_name: str, base_cidr: str = "10.0.0.0/16",
                                     tags: Dict[str, str] = None) -> "NetworkInfrastructureComposite":
        """
        Crea una arquitectura estándar con VPC y dos subredes privadas.
        """
        tags = tags or {}
        
        # Crear VPC con configuración estándar
        vpc = self.add_vpc(vpc_name, base_cidr, tags)
        
        # Agregar dos subredes privadas en diferentes AZs
        vpc.add_private_subnet(
            f"{vpc_name}_private_1", "10.0.1.0/24", "us-east-1a"
        ).add_private_subnet(
            f"{vpc_name}_private_2", "10.0.2.0/24", "us-east-1b"
        )
        
        # Agregar Internet Gateway
        vpc.add_internet_gateway()
        
        # Agregar tabla de rutas privada
        vpc.add_route_table(f"{vpc_name}_private_rt")
        
        return self
    
    def add_iam_resources(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los recursos IAM asociados.
        """
        return self.iam_module.export_resources()
    
    def export_complete_infrastructure(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Exporta toda la infraestructura incluyendo red e IAM.
        """
        return {
            "network_resources": self.export(),
            "iam_resources": self.add_iam_resources()
        }

class NetworkModuleBuilder:
    """
    Builder que utiliza el patrón Composite para crear
    módulos de red complejos de forma fluida.
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa el builder.
        
        Args:
            module_name: Nombre del módulo
        """
        self.module_name = module_name
        self.infrastructure = NetworkInfrastructureComposite(module_name)
    
    def with_private_network(self, vpc_name: str, 
                           subnet_count: int = 2,
                           base_cidr: str = "10.0.0.0/16",
                           tags: Dict[str, str] = None) -> "NetworkModuleBuilder":
        """
        Configura una red privada con el número especificado de subredes.
        """
        if subnet_count == 2:
            self.infrastructure.create_two_subnet_architecture(vpc_name, base_cidr, tags)
        else:
            # Crear VPC base
            vpc = self.infrastructure.add_vpc(vpc_name, base_cidr, tags)
            vpc.add_internet_gateway()
            
            # Crear subredes dinámicamente
            for i in range(subnet_count):
                subnet_cidr = f"10.0.{i+1}.0/24"
                az = f"us-east-{(i % 2) + 1}{'a' if i < 2 else 'b'}"
                vpc.add_private_subnet(f"{vpc_name}_private_{i+1}", subnet_cidr, az)
            
            # Agregar tabla de rutas
            vpc.add_route_table(f"{vpc_name}_private_rt")
        
        return self
    
    def build(self) -> NetworkInfrastructureComposite:
        """
        Construye y retorna la infraestructura completa.
        """
        return self.infrastructure 