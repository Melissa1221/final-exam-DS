import json
import os

import pytest
import requests
from pact import Consumer, Provider


class TestKubernetesApiContract:
    """pruebas contractuales para api de kubernetes"""

    @pytest.fixture
    def pact(self):
        """configurar pact para kubernetes api"""
        return Consumer("infrastructure-manager").has_pact_with(
            Provider("kubernetes-api"),
            host_name="localhost",
            port=8443,
            pact_dir="./pacts",
        )

    def test_get_cluster_info(self, pact):
        """verificar contrato para obtener informacion del cluster"""
        expected_response = {
            "cluster_name": "test-cluster",
            "node_count": 4,
            "kubernetes_version": "1.28.0",
            "status": "Ready",
        }

        (
            pact.given("cluster exists and is ready")
            .upon_receiving("request for cluster information")
            .with_request("GET", "/api/v1/cluster/info")
            .will_respond_with(200, body=expected_response)
        )

        with pact:
            response = requests.get("http://localhost:8443/api/v1/cluster/info")
            assert response.status_code == 200
            assert response.json()["cluster_name"] == "test-cluster"
            assert response.json()["node_count"] == 4

    def test_get_nodes_list(self, pact):
        """verificar contrato para listar nodos"""
        expected_nodes = {
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

        (
            pact.given("cluster has nodes")
            .upon_receiving("request for nodes list")
            .with_request("GET", "/api/v1/nodes")
            .will_respond_with(200, body=expected_nodes)
        )

        with pact:
            response = requests.get("http://localhost:8443/api/v1/nodes")
            assert response.status_code == 200
            nodes = response.json()["nodes"]
            assert len(nodes) >= 2
            assert any(node["type"] == "master" for node in nodes)

    def test_create_namespace(self, pact):
        """verificar contrato para crear namespace"""
        namespace_request = {
            "name": "test-namespace",
            "labels": {"environment": "test"},
        }

        expected_response = {
            "name": "test-namespace",
            "status": "Active",
            "created_at": "2024-01-01T00:00:00Z",
        }

        (
            pact.given("cluster is ready")
            .upon_receiving("request to create namespace")
            .with_request("POST", "/api/v1/namespaces", body=namespace_request)
            .will_respond_with(201, body=expected_response)
        )

        with pact:
            response = requests.post(
                "http://localhost:8443/api/v1/namespaces", json=namespace_request
            )
            assert response.status_code == 201
            assert response.json()["name"] == "test-namespace"

    def test_get_pods_status(self, pact):
        """verificar contrato para estado de pods"""
        expected_pods = {
            "pods": [
                {
                    "name": "nginx-demo-pod",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                }
            ]
        }

        (
            pact.given("pods are running")
            .upon_receiving("request for pods status")
            .with_request("GET", "/api/v1/pods?namespace=default")
            .will_respond_with(200, body=expected_pods)
        )

        with pact:
            response = requests.get(
                "http://localhost:8443/api/v1/pods?namespace=default"
            )
            assert response.status_code == 200
            pods = response.json()["pods"]
            assert len(pods) >= 1
            assert all(pod["ready"] for pod in pods)

    def test_service_health_check(self, pact):
        """verificar contrato para health check"""
        expected_health = {
            "status": "healthy",
            "components": {
                "api_server": "healthy",
                "etcd": "healthy",
                "scheduler": "healthy",
            },
        }

        (
            pact.given("cluster is healthy")
            .upon_receiving("health check request")
            .with_request("GET", "/healthz")
            .will_respond_with(200, body=expected_health)
        )

        with pact:
            response = requests.get("http://localhost:8443/healthz")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
