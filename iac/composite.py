"""Patrón Composite
Permite tratar múltiples recursos Terraform como una única unidad lógica o módulo compuesto.
"""

from typing import List, Dict, Any

class CompositeModule:
    """
    Clase que agrega múltiples diccionarios de recursos Terraform como un módulo lógico único.
    Sigue el patrón Composite, donde se unifican estructuras individuales en una sola jerarquía.
    """

    def __init__(self) -> None:
        """
        Inicializa la estructura compuesta como una lista vacía de recursos hijos.
        Cada hijo será un diccionario que contiene bloques Terraform
        """
        self._children: List[Dict[str, Any]] = []

    def add(self, resource_dict: Dict[str, Any]) -> None:
        """
        Agrega un diccionario de recurso al módulo
        """
        self._children.append(resource_dict)

    def export(self) -> Dict[str, Any]:
        """
        Exporta todos los recursos agregados en un único diccionario.
        """
        aggregated: Dict[str, Any] = {"resource": []}
        for child in self._children:
            # Combina ordenadamente todos los bloques resource de los hijos
            aggregated["resource"].extend(child.get("resource", []))
        return aggregated
