#!/usr/bin/env python3
"""
validaciones de politicas de seguridad para terraform
"""

import json
import sys
from pathlib import Path


def load_terraform_plan(plan_path):
    """cargar plan de terraform"""
    try:
        with open(plan_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"error cargando plan: {e}")
        return None


def get_resources(plan_data):
    """obtener recursos del plan"""
    if not plan_data or "planned_values" not in plan_data:
        return []

    root_module = plan_data["planned_values"].get("root_module", {})
    return root_module.get("resources", [])


def validate_resource_tags(resources):
    """verificar que recursos tengan tags obligatorios"""
    required_tags = ["Project", "Environment", "ManagedBy"]
    errors = []

    for resource in resources:
        if resource.get("type") != "null_resource":
            continue

        triggers = resource.get("values", {}).get("triggers", {})
        tags = triggers.get("tags", {})

        if not tags:
            continue  # skip recursos sin tags

        missing_tags = [tag for tag in required_tags if tag not in tags]
        if missing_tags:
            resource_name = resource.get("name", "unknown")
            errors.append(f"recurso {resource_name} sin tags: {missing_tags}")

    return errors


def validate_vpc_security(resources):
    """verificar configuracion segura de vpc"""
    errors = []

    vpc_resources = [
        r
        for r in resources
        if r.get("type") == "null_resource"
        and "vpc" in r.get("values", {}).get("triggers", {}).get("resource_type", "")
    ]

    for vpc in vpc_resources:
        triggers = vpc.get("values", {}).get("triggers", {})

        # verificar dns support
        if triggers.get("enable_dns_support") != "true":
            errors.append("vpc debe tener dns support habilitado")

        # verificar dns hostnames
        if triggers.get("enable_dns_hostnames") != "true":
            errors.append("vpc debe tener dns hostnames habilitado")

        # verificar cidr
        cidr = triggers.get("cidr_block", "")
        if not cidr or not cidr.startswith("10."):
            errors.append("vpc debe usar cidr privado (10.x.x.x)")

    return errors


def validate_subnet_security(resources):
    """verificar configuracion de subredes"""
    errors = []

    subnet_resources = [
        r
        for r in resources
        if r.get("type") == "null_resource"
        and "subnet" in r.get("values", {}).get("triggers", {}).get("resource_type", "")
    ]

    for subnet in subnet_resources:
        triggers = subnet.get("values", {}).get("triggers", {})

        # verificar que subnet tenga vpc dependency
        if not triggers.get("vpc_dependency"):
            errors.append("subnet debe tener vpc_dependency")

        # verificar cidr privado
        cidr = triggers.get("cidr_block", "")
        if not cidr or not cidr.startswith("10."):
            errors.append("subnet debe usar cidr privado")

    return errors


def validate_kubernetes_security(resources):
    """verificar configuracion segura de kubernetes"""
    errors = []

    k8s_resources = [
        r
        for r in resources
        if r.get("type") == "null_resource"
        and "kubernetes"
        in r.get("values", {}).get("triggers", {}).get("resource_type", "")
    ]

    for k8s in k8s_resources:
        triggers = k8s.get("values", {}).get("triggers", {})

        # verificar version de kubernetes
        version = triggers.get("kubernetes_version", "")
        if version and version < "1.25":
            errors.append("kubernetes version debe ser >= 1.25")

        # verificar que cluster tenga al menos 3 nodos
        total_nodes = triggers.get("total_nodes")
        if total_nodes and int(total_nodes) < 3:
            errors.append("cluster debe tener al menos 3 nodos")

    return errors


def validate_iam_security(resources):
    """verificar politicas iam"""
    errors = []

    iam_resources = [
        r
        for r in resources
        if r.get("type") == "null_resource"
        and r.get("values", {}).get("triggers", {}).get("resource_type", "")
        in ["iam_policy", "iam_role"]
    ]

    for iam in iam_resources:
        triggers = iam.get("values", {}).get("triggers", {})

        # verificar que politica tenga documento
        if not triggers.get("policy_document"):
            errors.append("politica iam debe tener documento")

        # verificar tipo de politica
        if not triggers.get("policy_type"):
            errors.append("politica iam debe tener tipo definido")

    return errors


def main():
    """validar politicas de seguridad"""
    if len(sys.argv) != 2:
        print("uso: python security.py <terraform_plan.json>")
        sys.exit(1)

    plan_path = sys.argv[1]
    plan_data = load_terraform_plan(plan_path)

    if not plan_data:
        sys.exit(1)

    resources = get_resources(plan_data)
    all_errors = []

    # ejecutar validaciones
    validations = [
        ("tags obligatorios", validate_resource_tags),
        ("seguridad vpc", validate_vpc_security),
        ("seguridad subnets", validate_subnet_security),
        ("seguridad kubernetes", validate_kubernetes_security),
        ("seguridad iam", validate_iam_security),
    ]

    for name, validation_func in validations:
        print(f"validando {name}...")
        errors = validation_func(resources)
        if errors:
            print(f"errores en {name}:")
            for error in errors:
                print(f"  - {error}")
            all_errors.extend(errors)
        else:
            print(f"  ok: {name}")

    if all_errors:
        print(f"\ntotal errores encontrados: {len(all_errors)}")
        sys.exit(1)
    else:
        print("\ntodas las validaciones de seguridad pasaron")
        sys.exit(0)


if __name__ == "__main__":
    main()
