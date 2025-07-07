"""
Módulo para crear roles, políticas y usuarios IAM ficticios
usando patrones Composite y Factory para reutilización.
"""

from typing import Dict, Any, List
import uuid
import json
from datetime import datetime

class IAMPolicyFactory:
    """
    Factory para crear políticas IAM simuladas.
    Implementa diferentes tipos de políticas comunes.
    """
    
    @staticmethod
    def create_ec2_policy(name: str, actions: List[str] = None,
                         resources: List[str] = None) -> Dict[str, Any]:
        """
        Crea una política IAM para recursos EC2.
        """
        actions = actions or ["ec2:DescribeInstances", "ec2:StartInstances", "ec2:StopInstances"]
        resources = resources or ["*"]
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": actions,
                    "Resource": resources
                }
            ]
        }
        
        triggers = {
            "resource_type": "iam_policy",
            "name": name,
            "policy_id": f"pol-{uuid.uuid4().hex[:8]}",
            "policy_document": json.dumps(policy_document),
            "policy_type": "ec2",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_policy_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_kubernetes_policy(name: str, cluster_name: str = None) -> Dict[str, Any]:
        """
        Crea una política IAM para recursos de Kubernetes.
        """
        actions = [
            "eks:DescribeCluster",
            "eks:ListClusters", 
            "eks:DescribeNodegroup",
            "eks:ListNodegroups"
        ]
        
        resources = [f"arn:aws:eks:*:*:cluster/{cluster_name}"] if cluster_name else ["*"]
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": actions,
                    "Resource": resources
                }
            ]
        }
        
        triggers = {
            "resource_type": "iam_policy",
            "name": name,
            "policy_id": f"pol-{uuid.uuid4().hex[:8]}",
            "policy_document": json.dumps(policy_document),
            "policy_type": "kubernetes",
            "cluster_dependency": cluster_name or "any",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_policy_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_network_policy(name: str, vpc_name: str = None) -> Dict[str, Any]:
        """
        Crea una política IAM para recursos de red.
        """
        actions = [
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeInternetGateways",
            "ec2:DescribeRouteTables",
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress"
        ]
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": actions,
                    "Resource": "*"
                }
            ]
        }
        
        triggers = {
            "resource_type": "iam_policy",
            "name": name,
            "policy_id": f"pol-{uuid.uuid4().hex[:8]}",
            "policy_document": json.dumps(policy_document),
            "policy_type": "network",
            "vpc_dependency": vpc_name or "any",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_policy_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class IAMRoleFactory:
    """
    Factory para crear roles IAM con diferentes configuraciones.
    """
    
    @staticmethod
    def create_service_role(name: str, service: str, 
                           policies: List[str] = None,
                           tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un rol IAM para un servicio específico.
        
        """
        tags = tags or {}
        policies = policies or []
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": f"{service}.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        triggers = {
            "resource_type": "iam_role",
            "name": name,
            "role_id": f"role-{uuid.uuid4().hex[:8]}",
            "arn": f"arn:aws:iam::123456789012:role/{name}",
            "service": service,
            "trust_policy": json.dumps(trust_policy),
            "attached_policies": str(policies),
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_role_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
    
    @staticmethod
    def create_user_role(name: str, policies: List[str] = None,
                        tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un rol IAM que puede ser asumido por usuarios.
        """
        tags = tags or {}
        policies = policies or []
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::123456789012:root"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        triggers = {
            "resource_type": "iam_role",
            "name": name,
            "role_id": f"role-{uuid.uuid4().hex[:8]}",
            "arn": f"arn:aws:iam::123456789012:role/{name}",
            "role_type": "user_assumable",
            "trust_policy": json.dumps(trust_policy),
            "attached_policies": str(policies),
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_role_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class IAMUserFactory:
    """
    Factory para crear usuarios IAM ficticios.
    """
    
    @staticmethod
    def create_service_user(name: str, policies: List[str] = None,
                           tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Crea un usuario IAM para servicios/aplicaciones.
        """
        tags = tags or {}
        policies = policies or []
        
        triggers = {
            "resource_type": "iam_user",
            "name": name,
            "user_id": f"user-{uuid.uuid4().hex[:8]}",
            "arn": f"arn:aws:iam::123456789012:user/{name}",
            "user_type": "service",
            "attached_policies": str(policies),
            "programmatic_access": "true",
            "console_access": "false",
            "created_at": datetime.utcnow().isoformat(),
            "tags": str(tags)
        }
        
        return {
            "resource": [{
                "null_resource": [{
                    f"iam_user_{name}": [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class IAMModule:
    """
    Módulo composite que agrupa políticas, roles y usuarios IAM
    para crear configuraciones completas reutilizables.
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa el módulo IAM.
        """
        self.module_name = module_name
        self.resources: List[Dict[str, Any]] = []
    
    def add_kubernetes_rbac(self, cluster_name: str, 
                           tags: Dict[str, str] = None) -> "IAMModule":
        """
        Agrega un conjunto completo de RBAC para Kubernetes.
        """
        tags = tags or {}
        
        # Política para administrador del cluster
        admin_policy = IAMPolicyFactory.create_kubernetes_policy(
            f"{cluster_name}_admin_policy", cluster_name
        )
        self.resources.append(admin_policy)
        
        # Rol para nodos del cluster
        node_role = IAMRoleFactory.create_service_role(
            f"{cluster_name}_node_role",
            "ec2",
            [f"{cluster_name}_admin_policy"],
            tags
        )
        self.resources.append(node_role)
        
        # Usuario de servicio para CI/CD
        service_user = IAMUserFactory.create_service_user(
            f"{cluster_name}_cicd_user",
            [f"{cluster_name}_admin_policy"],
            tags
        )
        self.resources.append(service_user)
        
        return self
    
    def add_network_rbac(self, vpc_name: str,
                        tags: Dict[str, str] = None) -> "IAMModule":
        """
        Agrega RBAC para gestión de red.
        """
        tags = tags or {}
        
        # Política para gestión de red
        network_policy = IAMPolicyFactory.create_network_policy(
            f"{vpc_name}_network_policy", vpc_name
        )
        self.resources.append(network_policy)
        
        # Rol para administrador de red
        network_admin_role = IAMRoleFactory.create_user_role(
            f"{vpc_name}_network_admin",
            [f"{vpc_name}_network_policy"],
            tags
        )
        self.resources.append(network_admin_role)
        
        return self
    
    def add_compute_rbac(self, compute_name: str,
                        tags: Dict[str, str] = None) -> "IAMModule":
        """
        Agrega RBAC para recursos de compute.
        """
        tags = tags or {}
        
        # Política para gestión de EC2
        compute_policy = IAMPolicyFactory.create_ec2_policy(
            f"{compute_name}_compute_policy"
        )
        self.resources.append(compute_policy)
        
        # Rol para instancias EC2
        instance_role = IAMRoleFactory.create_service_role(
            f"{compute_name}_instance_role",
            "ec2",
            [f"{compute_name}_compute_policy"],
            tags
        )
        self.resources.append(instance_role)
        
        return self
    
    def export_resources(self) -> List[Dict[str, Any]]:
        """
        Exporta todos los recursos del módulo.
        """
        return self.resources.copy() 