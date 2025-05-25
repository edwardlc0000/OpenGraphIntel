# tests/test_cloudenv.py

import pytest
import requests
from unittest.mock import patch, MagicMock
import backend.common.cloud_env

def test_detect_server_env():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert backend.common.cloud_env.detect_server_env() is True

def test_detect_server_env_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert backend.common.cloud_env.detect_server_env() is False

def test_detect_aws_metadata():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        assert backend.common.cloud_env.detect_aws_metadata() is True

def test_detect_aws_metadata_failure():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException
        assert backend.common.cloud_env.detect_aws_metadata() is False

