# backend/common/cloud_env.py

# Import dependencies
import logging
import os
import requests
from kubernetes import client, config
from kubernetes.client import CoreV1Api
from requests import Response


def detect_server_env() -> bool:
    """
    Detects if the code is running in a cloud environment.
    Returns:
        bool: True if running in a cloud environment, False otherwise.
    """
    try:
        response: Response = requests.get("http://169.254.169.254/", timeout=0.1)
        return response.status_code == 200
    except requests.RequestException:
        return False

def detect_server_provider() -> str | None:
    """
    Detects the cloud provider based on environment variables and metadata.
    Returns:
        str: The detected cloud provider.
    """
    if detect_aws_metadata():
        return "aws"
    elif detect_azure_metadata():
        return "azure"
    elif detect_gcp_metadata():
        return "gcp"
    else:
        return None

def detect_aws_metadata() -> bool:
    """
    Detects if the code is running in an Amazon Web Services (AWS) environment.
    """
    try:
        response: Response = requests.get("http://169.254.169.254/latest/meta-data/", timeout=0.1)
        return response.status_code == 200
    except requests.RequestException:
        return False

def detect_gcp_metadata() -> bool:
    """
    Detects if the code is running in a Google Cloud Platform (GCP) environment.
    """
    try:
        response: Response = requests.get("http://metadata.google.internal/computeMetadata/v1/", headers={"Metadata-Flavor": "Google"}, timeout=0.1)
        return response.status_code == 200
    except requests.RequestException:
        return False

def detect_azure_metadata() -> bool:
    """
    Detects if the code is running in an Microsoft Azure environment.
    """
    try:
        response: Response = requests.get("http://169.254.169.254/metadata/instance?api-version=2021-02-01", headers={"Metadata": "true"}, timeout=0.1)
        return response.status_code == 200
    except requests.RequestException:
        return False

def detect_k8s_env() -> bool:
    """
    Detects if the code is running in a Kubernetes environment.
    """
    return os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount") or os.path.exists("/var/run/secrets/kubernetes.io/namespace")

def detect_k8s_provider() -> str | None:
    """
    Detects the Kubernetes provider based on the environment.
    Returns:
        str: The detected Kubernetes provider.
    """
    try:
        config.load_incluster_config()
        v1: CoreV1Api = client.CoreV1Api()
        pod_name: str = os.getenv("HOSTNAME")
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            namespace: str = f.read().strip()

        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        node_name = pod.spec.node_name
        node = v1.read_node(name=node_name)
        labels = node.metadata.labels

        if "eks.amazonaws.com/nodegroup" in labels:
            return "aws-eks"
        elif "kubernetes.azure.com/cluster" in labels:
            return "azure-aks"
        elif "cloud.google.com/gke-nodepool" in labels:
            return "gcp-gke"
        else:
            return None

    except Exception as e:
        return None

def detect_serverless_provider() -> str | None:
    """
    Detects the serverless environment based on environment variables.
    Returns:
        str: The detected serverless environment.
    """
    if "AWS_EXECUTION_ENV" in os.environ:
        return "aws-lambda"
    elif "AZURE_FUNCTIONS_ENVIRONMENT" in os.environ:
        return "azure-functions"
    elif "FUNCTION_NAME" in os.environ:
        return "gcp-cloud-functions"
    else:
        return None

def detect_cloud_env() -> str:
    """
    Detects the environment in which the code is running.
    Returns:
        str: The detected environment.
    """
    return_value: str | None = detect_k8s_provider()
    if return_value is not None:
        return return_value
    return_value: str | None = detect_server_provider()
    if return_value is not None:
        return return_value
    return_value: str | None = detect_serverless_provider()
    if return_value is not None:
        return return_value
    raise RuntimeError("Unsupported environment. Please check your cloud provider or serverless configuration.")
