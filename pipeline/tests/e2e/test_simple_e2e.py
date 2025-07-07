import time

import pytest
import requests


class TestSimpleE2E:
    """pruebas end-to-end simplificadas"""

    def test_kubernetes_master_responds(self):
        """verificar que el master de kubernetes responda"""
        response = requests.get("http://localhost:6443/healthz", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert data.get("status") == "healthy"

    def test_kubernetes_worker_responds(self):
        """verificar que el worker responda"""
        response = requests.get("http://localhost:10250/healthz", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert data.get("status") == "healthy"

    def test_nginx_demo_application(self):
        """verificar que la aplicacion nginx funcione"""
        response = requests.get("http://localhost:8080/", timeout=10)
        assert response.status_code == 200

        # verificar que el contenido sea html o tenga nginx
        content = response.text.lower()
        assert "nginx" in content or "html" in content

    def test_prometheus_metrics(self):
        """verificar que prometheus responda"""
        # verificar health endpoint
        response = requests.get("http://localhost:9090/-/healthy", timeout=10)
        assert response.status_code == 200

    def test_all_services_integration(self):
        """test de integracion de todos los servicios"""
        services = [
            ("k8s-master", "http://localhost:6443/healthz"),
            ("k8s-worker", "http://localhost:10250/healthz"),
            ("nginx-demo", "http://localhost:8080/"),
            ("prometheus", "http://localhost:9090/-/healthy"),
        ]

        for service_name, service_url in services:
            try:
                response = requests.get(service_url, timeout=10)
                assert (
                    response.status_code == 200
                ), f"{service_name} no responde correctamente"
                print(f"✓ {service_name} ok")
            except Exception as e:
                pytest.fail(f"{service_name} fallo: {e}")

    def test_service_response_time(self):
        """verificar tiempos de respuesta aceptables"""
        services = [
            "http://localhost:6443/healthz",
            "http://localhost:10250/healthz",
            "http://localhost:8080/",
        ]

        for service_url in services:
            start_time = time.time()
            response = requests.get(service_url, timeout=10)
            response_time = time.time() - start_time

            assert response.status_code == 200
            assert (
                response_time < 2.0
            ), f"servicio {service_url} muy lento: {response_time}s"
