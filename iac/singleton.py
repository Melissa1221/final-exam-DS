"""Patrón Singleton

Asegura que una clase tenga una única instancia global, compartida en todo el sistema.
Esta implementación es segura para entornos con múltiples hilos (thread-safe).
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict


class SingletonMeta(type):
    """
    Asegura que todas las instancias de la clase que use esta metaclase
    compartan el mismo objeto (único en memoria).
    """

    _instances: Dict[type, "ConfigSingleton"] = {}
    _lock: threading.Lock = threading.Lock()  # Controla el acceso concurrente

    def __call__(cls, *args, **kwargs):
        """
        Controla la creación de instancias: solo permite una única instancia por clase.
        Si ya existe, devuelve la existente. Si no, la crea protegida por un lock.
        """
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigSingleton(metaclass=SingletonMeta):
    """
    Clase Singleton que actúa como contenedor de configuración global.
    Todas las clases del sistema pueden consultar y modificar esta configuración compartida.
    """

    def __init__(self, env_name: str = "default") -> None:
        """
        Inicializa la configuración con un nombre de entorno y un timestamp de creación.
        """
        self.env_name = env_name
        self.created_at = datetime.now(tz=timezone.utc).isoformat()  # Fecha de creación
        self.settings: Dict[str, Any] = {}  # Diccionario para guardar claves y valores

    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor en la configuración global.
        """
        self.settings[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Recupera un valor de la configuración global.
        """
        return self.settings.get(key, default)
