import os
import time
import pytest
import requests
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class TestInfrastructureE2E:
    """pruebas end-to-end para infraestructura completa"""

    @pytest.fixture(autouse=True)
    def setup_session(self):
        """configurar sesion http con reintentos"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def test_kubernetes_master_health(self):
        """verificar que el nodo master responda"""
        master_url = os.getenv('K8S_MASTER_URL', 'http://localhost:6443')
        
        response = self.session.get(f"{master_url}/healthz", timeout=10)
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data.get('status') == 'healthy'

    def test_kubernetes_workers_health(self):
        """verificar que los nodos worker respondan"""
        worker_1_url = os.getenv('K8S_WORKER_1_URL', 'http://localhost:10250')
        worker_2_url = os.getenv('K8S_WORKER_2_URL', 'http://localhost:10251')
        
        for worker_url in [worker_1_url, worker_2_url]:
            response = self.session.get(f"{worker_url}/healthz", timeout=10)
            assert response.status_code == 200

    def test_nginx_demo_application(self):
        """verificar que la aplicacion nginx demo responda"""
        nginx_url = os.getenv('NGINX_DEMO_URL', 'http://localhost:8080')
        
        response = self.session.get(nginx_url, timeout=10)
        assert response.status_code == 200
        
        # verificar contenido basico
        content = response.text
        assert 'nginx' in content.lower() or 'welcome' in content.lower()

    def test_prometheus_metrics(self):
        """verificar que prometheus este recolectando metricas"""
        prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        
        # verificar health endpoint
        health_response = self.session.get(f"{prometheus_url}/-/healthy", timeout=10)
        assert health_response.status_code == 200
        
        # verificar que tenga metricas
        metrics_response = self.session.get(f"{prometheus_url}/api/v1/query?query=up", timeout=10)
        assert metrics_response.status_code == 200
        
        metrics_data = metrics_response.json()
        assert metrics_data.get('status') == 'success'

    def test_grafana_dashboard(self):
        """verificar que grafana responda correctamente"""
        grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
        
        # verificar health endpoint
        health_response = self.session.get(f"{grafana_url}/api/health", timeout=15)
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert health_data.get('database') == 'ok'

    def test_bastion_host_ssh(self):
        """verificar que el bastion host tenga ssh disponible"""
        bastion_host = os.getenv('BASTION_HOST', 'localhost')
        bastion_port = int(os.getenv('BASTION_PORT', '2222'))
        
        # verificar que el puerto ssh este abierto
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            result = sock.connect_ex((bastion_host, bastion_port))
            assert result == 0, f"puerto ssh {bastion_port} no esta disponible"
        finally:
            sock.close()

    def test_service_connectivity_chain(self):
        """verificar conectividad entre servicios"""
        # verificar que prometheus puede hacer scraping
        prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        
        # consultar targets
        targets_response = self.session.get(
            f"{prometheus_url}/api/v1/targets", 
            timeout=10
        )
        assert targets_response.status_code == 200
        
        targets_data = targets_response.json()
        assert targets_data.get('status') == 'success'

    def test_full_infrastructure_integration(self):
        """test de integracion completa de la infraestructura"""
        # verificar que todos los servicios principales esten up
        services = [
            ('k8s-master', os.getenv('K8S_MASTER_URL', 'http://localhost:6443')),
            ('nginx-demo', os.getenv('NGINX_DEMO_URL', 'http://localhost:8080')),
            ('prometheus', os.getenv('PROMETHEUS_URL', 'http://localhost:9090')),
            ('grafana', os.getenv('GRAFANA_URL', 'http://localhost:3000')),
        ]
        
        service_status = {}
        
        for service_name, service_url in services:
            try:
                if service_name == 'k8s-master':
                    response = self.session.get(f"{service_url}/healthz", timeout=10)
                elif service_name == 'prometheus':
                    response = self.session.get(f"{service_url}/-/healthy", timeout=10)
                elif service_name == 'grafana':
                    response = self.session.get(f"{service_url}/api/health", timeout=15)
                else:
                    response = self.session.get(service_url, timeout=10)
                
                service_status[service_name] = response.status_code == 200
                
            except Exception as e:
                service_status[service_name] = False
                print(f"error checking {service_name}: {e}")
        
        # verificar que todos los servicios esten funcionando
        failed_services = [name for name, status in service_status.items() if not status]
        assert not failed_services, f"servicios fallaron: {failed_services}"
        
        print(f"todos los servicios estan funcionando: {list(service_status.keys())}")

    def test_load_balancing_simulation(self):
        """simular balanceador de carga entre workers"""
        worker_1_url = os.getenv('K8S_WORKER_1_URL', 'http://localhost:10250')
        worker_2_url = os.getenv('K8S_WORKER_2_URL', 'http://localhost:10251')
        
        # hacer varias peticiones a ambos workers
        for _ in range(5):
            for worker_url in [worker_1_url, worker_2_url]:
                response = self.session.get(f"{worker_url}/healthz", timeout=5)
                assert response.status_code == 200
                
                # simular delay de red
                time.sleep(0.1)

    def test_monitoring_data_flow(self):
        """verificar flujo de datos de monitoring"""
        prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
        
        # verificar que prometheus tenga metricas
        metrics_response = self.session.get(
            f"{prometheus_url}/api/v1/query?query=prometheus_build_info", 
            timeout=10
        )
        assert metrics_response.status_code == 200
        
        # verificar que grafana este conectado
        health_response = self.session.get(f"{grafana_url}/api/health", timeout=15)
        assert health_response.status_code == 200 