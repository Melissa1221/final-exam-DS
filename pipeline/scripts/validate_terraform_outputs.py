#!/usr/bin/env python3
"""
validador de outputs de terraform plan
verifica que el plan contenga los recursos esperados
"""

import json
import subprocess
import sys
from typing import Any, Dict, List


class TerraformPlanValidator:
    """validador para planes de terraform"""

    def __init__(self, plan_file: str):
        """inicializar validador con archivo de plan"""
        self.plan_file = plan_file
        self.plan_data = self._load_plan()

    def _load_plan(self) -> Dict[str, Any]:
        """cargar y parsear el plan de terraform"""
        try:
            # convertir plan binario a json
            result = subprocess.run(
                ["terraform", "show", "-json", self.plan_file],
                capture_output=True,
                text=True,
                check=True,
            )

            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"error al leer plan: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"error al parsear json del plan: {e}")
            sys.exit(1)

    def validate_resource_count(self, expected_count: int) -> bool:
        """validar numero total de recursos"""
        if "planned_values" not in self.plan_data:
            print("plan no contiene planned_values")
            return False

        root_module = self.plan_data["planned_values"].get("root_module", {})
        resources = root_module.get("resources", [])

        actual_count = len(resources)
        if actual_count != expected_count:
            print(f"recursos esperados: {expected_count}, encontrados: {actual_count}")
            return False

        print(f"validacion de conteo exitosa: {actual_count} recursos")
        return True

    def validate_vpc_resources(self) -> bool:
        """validar recursos de vpc"""
        resources = self._get_resources()

        # buscar recursos vpc
        vpc_resources = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and "vpc"
            in r.get("values", {}).get("triggers", {}).get("resource_type", "")
        ]

        if not vpc_resources:
            print("no se encontraron recursos vpc")
            return False

        # validar vpc tiene cidr
        vpc = vpc_resources[0]
        triggers = vpc.get("values", {}).get("triggers", {})

        if "cidr_block" not in triggers:
            print("vpc no tiene cidr_block")
            return False

        print(f"vpc validado con cidr: {triggers['cidr_block']}")
        return True

    def validate_subnet_resources(self) -> bool:
        """validar recursos de subnet"""
        resources = self._get_resources()

        # buscar recursos subnet
        subnet_resources = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and "subnet"
            in r.get("values", {}).get("triggers", {}).get("resource_type", "")
        ]

        if len(subnet_resources) < 2:
            print(
                f"se esperaban al menos 2 subredes, encontradas: {len(subnet_resources)}"
            )
            return False

        # validar cada subnet tiene vpc_dependency
        for subnet in subnet_resources:
            triggers = subnet.get("values", {}).get("triggers", {})
            if "vpc_dependency" not in triggers:
                print("subnet sin vpc_dependency")
                return False

        print(f"validadas {len(subnet_resources)} subredes")
        return True

    def validate_kubernetes_resources(self) -> bool:
        """validar recursos de kubernetes"""
        resources = self._get_resources()

        # buscar cluster de kubernetes
        k8s_cluster = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and "kubernetes_cluster"
            in r.get("values", {}).get("triggers", {}).get("resource_type", "")
        ]

        if not k8s_cluster:
            print("no se encontro cluster de kubernetes")
            return False

        cluster = k8s_cluster[0]
        triggers = cluster.get("values", {}).get("triggers", {})

        # validar propiedades del cluster
        required_fields = ["total_nodes", "kubernetes_version", "cluster_type"]
        for field in required_fields:
            if field not in triggers:
                print(f"cluster sin campo requerido: {field}")
                return False

        # validar nodos de kubernetes
        k8s_nodes = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and r.get("values", {}).get("triggers", {}).get("resource_type", "")
            in ["kubernetes_master", "kubernetes_node"]
        ]

        if len(k8s_nodes) < 4:  # 1 master + 3 workers
            print(f"se esperaban al menos 4 nodos k8s, encontrados: {len(k8s_nodes)}")
            return False

        print(f"validado cluster kubernetes con {len(k8s_nodes)} nodos")
        return True

    def validate_iam_resources(self) -> bool:
        """validar recursos iam"""
        resources = self._get_resources()

        # buscar recursos iam
        iam_resources = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and r.get("values", {}).get("triggers", {}).get("resource_type", "")
            in ["iam_policy", "iam_role", "iam_user"]
        ]

        if not iam_resources:
            print("no se encontraron recursos iam")
            return False

        # validar tipos de recursos iam
        iam_types = set()
        for resource in iam_resources:
            iam_type = (
                resource.get("values", {}).get("triggers", {}).get("resource_type", "")
            )
            iam_types.add(iam_type)

        expected_types = {"iam_policy", "iam_role"}
        if not expected_types.issubset(iam_types):
            print(f"tipos iam faltantes: {expected_types - iam_types}")
            return False

        print(f"validados {len(iam_resources)} recursos iam")
        return True

    def validate_compute_resources(self) -> bool:
        """validar recursos de compute adicionales"""
        resources = self._get_resources()

        # buscar recursos de compute
        compute_resources = [
            r
            for r in resources
            if r.get("type") == "null_resource"
            and r.get("values", {}).get("triggers", {}).get("resource_type", "")
            in ["virtual_machine", "container"]
        ]

        if not compute_resources:
            print("no se encontraron recursos de compute adicionales")
            return False

        print(f"validados {len(compute_resources)} recursos de compute")
        return True

    def _get_resources(self) -> List[Dict[str, Any]]:
        """obtener lista de recursos del plan"""
        if "planned_values" not in self.plan_data:
            return []

        root_module = self.plan_data["planned_values"].get("root_module", {})
        return root_module.get("resources", [])

    def validate_all(self) -> bool:
        """ejecutar todas las validaciones"""
        validations = [
            ("conteo de recursos", lambda: self.validate_resource_count(27)),
            ("recursos vpc", self.validate_vpc_resources),
            ("recursos subnet", self.validate_subnet_resources),
            ("recursos kubernetes", self.validate_kubernetes_resources),
            ("recursos iam", self.validate_iam_resources),
            ("recursos compute", self.validate_compute_resources),
        ]

        all_passed = True

        for name, validation_func in validations:
            print(f"validando {name}...")
            try:
                if not validation_func():
                    print(f"fallo: {name}")
                    all_passed = False
                else:
                    print(f"exito: {name}")
            except Exception as e:
                print(f"error en {name}: {e}")
                all_passed = False

        return all_passed


def main():
    """funcion principal"""
    if len(sys.argv) != 2:
        print("uso: python validate_terraform_outputs.py <plan_file>")
        sys.exit(1)

    plan_file = sys.argv[1]
    validator = TerraformPlanValidator(plan_file)

    print("iniciando validacion del plan de terraform...")

    if validator.validate_all():
        print("todas las validaciones pasaron exitosamente")
        sys.exit(0)
    else:
        print("algunas validaciones fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
