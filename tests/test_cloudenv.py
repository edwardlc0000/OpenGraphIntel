# tests/test_cloudenv.py

import pytest
import requests
from unittest.mock import patch, MagicMock
import backend.common.cloud_env as cloud_env

def test_detect_server_env():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert cloud_env.detect_server_env() is True

def test_detect_server_env_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert cloud_env.detect_server_env() is False

def test_detect_aws_metadata():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert cloud_env.detect_aws_metadata() is True

def test_detect_aws_metadata_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert cloud_env.detect_aws_metadata() is False

def test_detect_azure_metadata():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert cloud_env.detect_azure_metadata() is True

def test_detect_azure_metadata_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert cloud_env.detect_azure_metadata() is False

def test_dectect_gcp_metadata():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert cloud_env.detect_gcp_metadata() is True

def test_detect_gcp_metadata_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert cloud_env.detect_gcp_metadata() is False

def test_detect_server_provider_aws():
    with patch('backend.common.cloud_env.detect_aws_metadata', return_value=True):
        assert cloud_env.detect_server_provider() == "aws"

def test_detect_server_provider_azure():
    with patch('backend.common.cloud_env.detect_azure_metadata', return_value=True):
        assert cloud_env.detect_server_provider() == "azure"

def test_detect_server_provider_gcp():
    with patch('backend.common.cloud_env.detect_gcp_metadata', return_value=True):
        assert cloud_env.detect_server_provider() == "gcp"

def test_detect_server_provider_unsupported():
    with patch('backend.common.cloud_env.detect_aws_metadata', return_value=False), \
         patch('backend.common.cloud_env.detect_azure_metadata', return_value=False), \
         patch('backend.common.cloud_env.detect_gcp_metadata', return_value=False):
        with pytest.raises(RuntimeError, match="Unsupported cloud provider detected."):
            cloud_env.detect_server_provider()

def test_detect_k8s_env():
    with patch('os.path.exists', return_value=True):
        assert cloud_env.detect_k8s_env() is True

def test_detect_k8s_env_failure():
    with patch('os.path.exists', return_value=False):
        assert cloud_env.detect_k8s_env() is False

def test_detect_k8s_provider_aws(mocker):
    # Mock the Kubernetes API calls and environment
    mocker.patch('kubernetes.config.load_incluster_config')
    mocker.patch('os.getenv', return_value='test-pod')
    mocker.patch('builtins.open', mocker.mock_open(read_data='test-namespace'))

    # Mock CoreV1Api to return a pod with a specific node name
    mock_core_v1_api = mocker.patch('kubernetes.client.CoreV1Api')
    mock_pod = MagicMock()
    mock_pod.spec.node_name = 'test-node'
    mock_core_v1_api.return_value.read_namespaced_pod.return_value = mock_pod

    # Mock node information to simulate AWS EKS
    mock_node = MagicMock()
    mock_node.metadata.labels = {"eks.amazonaws.com/nodegroup": "my-node-group"}
    mock_core_v1_api.return_value.read_node.return_value = mock_node

    assert cloud_env.detect_k8s_provider() == "aws-eks"

def test_detect_k8s_provider_azure(mocker):
    # Mock the Kubernetes API calls and environment
    mocker.patch('kubernetes.config.load_incluster_config')
    mocker.patch('os.getenv', return_value='test-pod')
    mocker.patch('builtins.open', mocker.mock_open(read_data='test-namespace'))

    # Mock CoreV1Api to return a pod with a specific node name
    mock_core_v1_api = mocker.patch('kubernetes.client.CoreV1Api')
    mock_pod = MagicMock()
    mock_pod.spec.node_name = 'test-node'
    mock_core_v1_api.return_value.read_namespaced_pod.return_value = mock_pod

    # Mock node information to simulate Azure AKS
    mock_node = MagicMock()
    mock_node.metadata.labels = {"kubernetes.azure.com/cluster": "my-cluster"}
    mock_core_v1_api.return_value.read_node.return_value = mock_node

    assert cloud_env.detect_k8s_provider() == "azure-aks"

def test_detect_k8s_provider_gcp(mocker):
    # Mock the Kubernetes API calls and environment
    mocker.patch('kubernetes.config.load_incluster_config')
    mocker.patch('os.getenv', return_value='test-pod')
    mocker.patch('builtins.open', mocker.mock_open(read_data='test-namespace'))

    # Mock CoreV1Api to return a pod with a specific node name
    mock_core_v1_api = mocker.patch('kubernetes.client.CoreV1Api')
    mock_pod = MagicMock()
    mock_pod.spec.node_name = 'test-node'
    mock_core_v1_api.return_value.read_namespaced_pod.return_value = mock_pod

    # Mock node information to simulate GCP GKE
    mock_node = MagicMock()
    mock_node.metadata.labels = {"cloud.google.com/gke-nodepool": "my-node-pool"}
    mock_core_v1_api.return_value.read_node.return_value = mock_node

    assert cloud_env.detect_k8s_provider() == "gcp-gke"

def test_detect_k8s_provider_unsupported(mocker):
    # Mock the Kubernetes API calls and environment
    mocker.patch('kubernetes.config.load_incluster_config')
    mocker.patch('os.getenv', return_value='test-pod')
    mocker.patch('builtins.open', mocker.mock_open(read_data='test-namespace'))

    # Mock CoreV1Api to return a pod with a specific node name
    mock_core_v1_api = mocker.patch('kubernetes.client.CoreV1Api')
    mock_pod = MagicMock()
    mock_pod.spec.node_name = 'test-node'
    mock_core_v1_api.return_value.read_namespaced_pod.return_value = mock_pod

    # Mock node information to simulate an unsupported provider
    mock_node = MagicMock()
    mock_node.metadata.labels = {"unsupported.label": "value"}
    mock_core_v1_api.return_value.read_node.return_value = mock_node

    with pytest.raises(RuntimeError, match="Unsupported Kubernetes provider detected."):
        cloud_env.detect_k8s_provider()

def test_detect_severless_env_aws(monkeypatch):
    monkeypatch.setenv("AWS_EXECUTION_ENV", "test_function")
    assert "aws" in cloud_env.detect_serverless_env()

def test_detect_severless_env_azure(monkeypatch):
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "test_environment")
    assert "azure" in cloud_env.detect_serverless_env()

def test_detect_severless_env_gcp(monkeypatch):
    monkeypatch.setenv("FUNCTION_NAME", "test_function")
    assert "gcp" in cloud_env.detect_serverless_env()

def test_detect_severless_env_unsupported():
    with pytest.raises(RuntimeError, match="Unsupported cloud provider detected."):
        cloud_env.detect_serverless_env()

@patch('backend.common.cloud_env.detect_server_provider')
@patch('backend.common.cloud_env.detect_server_env')
def test_detect_env_aws_server(mock_detect_server_env, mock_detect_server_provider):
    mock_detect_server_env.return_value = True
    mock_detect_server_provider.return_value = "aws"
    assert cloud_env.detect_env() == "aws"

@patch('backend.common.cloud_env.detect_k8s_provider')
@patch('backend.common.cloud_env.detect_k8s_env')
def test_detect_env_aws_k8s(mock_detect_k8s_env, mock_detect_k8s_provider):
    mock_detect_k8s_env.return_value = True
    mock_detect_k8s_provider.return_value = "aws-eks"
    assert cloud_env.detect_env() == "aws-eks"

@patch('backend.common.cloud_env.detect_serverless_env')
def test_detect_env_aws_lambda(mock_detect_serverless_env):
    mock_detect_serverless_env.return_value = "aws-lambda"
    assert cloud_env.detect_env() == "aws-lambda"

@patch('backend.common.cloud_env.detect_server_provider')
@patch('backend.common.cloud_env.detect_server_env')
def test_detect_env_azure(mock_detect_server_env, mock_detect_server_provider):
    mock_detect_server_env.return_value = True
    mock_detect_server_provider.return_value = "azure"
    assert cloud_env.detect_env() == "azure"

@patch('backend.common.cloud_env.detect_k8s_provider')
@patch('backend.common.cloud_env.detect_k8s_env')
def test_detect_env_azure_k8s(mock_detect_k8s_env, mock_detect_k8s_provider):
    mock_detect_k8s_env.return_value = True
    mock_detect_k8s_provider.return_value = "azure-aks"
    assert cloud_env.detect_env() == "azure-aks"

@patch('backend.common.cloud_env.detect_serverless_env')
def test_detect_env_azure_functions(mock_detect_serverless_env):
    mock_detect_serverless_env.return_value = "azure-functions"
    assert cloud_env.detect_env() == "azure-functions"

@patch('backend.common.cloud_env.detect_server_provider')
@patch('backend.common.cloud_env.detect_server_env')
def test_detect_env_gcp(mock_detect_server_env, mock_detect_server_provider):
    mock_detect_server_env.return_value = True
    mock_detect_server_provider.return_value = "gcp"
    assert cloud_env.detect_env() == "gcp"

@patch('backend.common.cloud_env.detect_k8s_provider')
@patch('backend.common.cloud_env.detect_k8s_env')
def test_detect_env_gcp_k8s(mock_detect_k8s_env, mock_detect_k8s_provider):
    mock_detect_k8s_env.return_value = True
    mock_detect_k8s_provider.return_value = "gcp-gke"
    assert cloud_env.detect_env() == "gcp-gke"

@patch('backend.common.cloud_env.detect_serverless_env')
def test_detect_env_gcp_functions(mock_detect_serverless_env):
    mock_detect_serverless_env.return_value = "gcp-cloud-functions"
    assert cloud_env.detect_env() == "gcp-cloud-functions"

def test_detect_env_unsupported():
    with patch('backend.common.cloud_env.detect_k8s_env', return_value=False), \
         patch('backend.common.cloud_env.detect_server_env', return_value=False):
        with pytest.raises(RuntimeError, match="Unsupported cloud provider detected."):
            cloud_env.detect_env()