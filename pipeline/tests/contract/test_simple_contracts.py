import json

import pytest
import requests
import responses


class TestInfrastructureContracts:
    """pruebas simples de contratos para apis de infraestructura"""

    @responses.activate
    def test_kubernetes_api_cluster_info(self):
        """verificar contrato de informacion del cluster"""
        expected_response = {
            "cluster_name": "test-cluster",
            "node_count": 4,
            "kubernetes_version": "1.28.0",
            "status": "Ready",
        }

        responses.add(
            responses.GET,
            "http://localhost:8443/api/v1/cluster/info",
            json=expected_response,
            status=200,
        )

        response = requests.get("http://localhost:8443/api/v1/cluster/info")

        assert response.status_code == 200
        data = response.json()
        assert data["cluster_name"] == "test-cluster"
        assert data["node_count"] == 4
        assert data["kubernetes_version"] == "1.28.0"
        assert data["status"] == "Ready"

    @responses.activate
    def test_kubernetes_api_nodes_list(self):
        """verificar contrato de lista de nodos"""
        expected_response = {
            "nodes": [
                {
                    "name": "master-node",
                    "type": "master",
                    "status": "Ready",
                    "ip": "10.0.1.10",
                },
                {
                    "name": "worker-node-1",
                    "type": "worker",
                    "status": "Ready",
                    "ip": "10.0.1.11",
                },
            ]
        }

        responses.add(
            responses.GET,
            "http://localhost:8443/api/v1/nodes",
            json=expected_response,
            status=200,
        )

        response = requests.get("http://localhost:8443/api/v1/nodes")

        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 2
        assert any(node["type"] == "master" for node in data["nodes"])
        assert any(node["type"] == "worker" for node in data["nodes"])

    @responses.activate
    def test_kubernetes_api_health_check(self):
        """verificar contrato de health check"""
        expected_response = {
            "status": "healthy",
            "components": {
                "api_server": "healthy",
                "etcd": "healthy",
                "scheduler": "healthy",
            },
        }

        responses.add(
            responses.GET,
            "http://localhost:8443/healthz",
            json=expected_response,
            status=200,
        )

        response = requests.get("http://localhost:8443/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["api_server"] == "healthy"

    @responses.activate
    def test_network_api_vpc_info(self):
        """verificar contrato de informacion de vpc"""
        expected_response = {
            "vpc_id": "vpc-12345",
            "cidr_block": "10.0.0.0/16",
            "subnets": [
                {
                    "subnet_id": "subnet-1",
                    "cidr_block": "10.0.1.0/24",
                    "availability_zone": "us-east-1a",
                },
                {
                    "subnet_id": "subnet-2",
                    "cidr_block": "10.0.2.0/24",
                    "availability_zone": "us-east-1b",
                },
            ],
        }

        responses.add(
            responses.GET,
            "http://localhost:9090/api/v1/network/vpc",
            json=expected_response,
            status=200,
        )

        response = requests.get("http://localhost:9090/api/v1/network/vpc")

        assert response.status_code == 200
        data = response.json()
        assert data["vpc_id"] == "vpc-12345"
        assert data["cidr_block"] == "10.0.0.0/16"
        assert len(data["subnets"]) == 2

    @responses.activate
    def test_application_health_endpoint(self):
        """verificar contrato de aplicacion nginx"""
        expected_response = {
            "status": "healthy",
            "service": "nginx-demo",
            "version": "1.0.0",
        }

        responses.add(
            responses.GET,
            "http://localhost:8080/health",
            json=expected_response,
            status=200,
        )

        response = requests.get("http://localhost:8080/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "nginx-demo"

    def test_contract_structure_validation(self):
        """verificar que las respuestas tengan estructura correcta"""
        # definir esquemas esperados
        k8s_cluster_schema = {
            "cluster_name": str,
            "node_count": int,
            "kubernetes_version": str,
            "status": str,
        }

        # ejemplo de validacion de estructura
        test_data = {
            "cluster_name": "test-cluster",
            "node_count": 4,
            "kubernetes_version": "1.28.0",
            "status": "Ready",
        }

        # verificar tipos
        for key, expected_type in k8s_cluster_schema.items():
            assert key in test_data
            assert isinstance(test_data[key], expected_type)

    def test_error_responses_contract(self):
        """verificar contratos de respuestas de error"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://localhost:8443/api/v1/invalid",
                json={"error": "not found", "status": 404},
                status=404,
            )

            response = requests.get("http://localhost:8443/api/v1/invalid")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["status"] == 404
