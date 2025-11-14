"""
Shared pytest fixtures for Network Traffic Analyzer tests.

This module provides common fixtures used across all test modules.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import pytest
import numpy as np
import pandas as pd
from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_packet():
    """Create a sample network packet for testing."""
    return Ether()/IP(src="192.168.1.100", dst="192.168.1.1")/TCP(sport=12345, dport=80)/Raw(load=b"GET / HTTP/1.1")


@pytest.fixture
def sample_packets():
    """Create multiple sample packets for testing."""
    packets = []

    # HTTP packet
    packets.append(
        Ether()/IP(src="192.168.1.100", dst="192.168.1.1")/TCP(sport=12345, dport=80)/Raw(load=b"GET / HTTP/1.1")
    )

    # HTTPS packet
    packets.append(
        Ether()/IP(src="192.168.1.100", dst="192.168.1.1")/TCP(sport=12346, dport=443)
    )

    # DNS packet (UDP)
    packets.append(
        Ether()/IP(src="192.168.1.100", dst="8.8.8.8")/UDP(sport=53, dport=53)
    )

    # ICMP packet
    packets.append(
        Ether()/IP(src="192.168.1.100", dst="8.8.8.8")/ICMP()
    )

    # SSH packet
    packets.append(
        Ether()/IP(src="192.168.1.100", dst="192.168.1.50")/TCP(sport=54321, dport=22)
    )

    return packets


@pytest.fixture
def sample_pcap_file(temp_dir, sample_packets):
    """Create a sample PCAP file for testing."""
    from scapy.all import wrpcap

    pcap_path = temp_dir / "test.pcap"
    wrpcap(str(pcap_path), sample_packets)
    return pcap_path


@pytest.fixture
def sample_features():
    """Create sample feature data for testing."""
    return {
        'packet_length': 100,
        'protocol_type': 6,  # TCP
        'src_port': 12345,
        'dst_port': 80,
        'tcp_flags': 2,
        'payload_size': 50,
        'header_length': 50,
        'window_size': 65535,
        'time_delta': 0.1,
        'packet_rate': 10.0,
    }


@pytest.fixture
def sample_features_dataframe():
    """Create sample feature DataFrame for testing."""
    data = {
        'packet_length': [100, 150, 200, 80, 120],
        'protocol_type': [6, 6, 17, 1, 6],
        'src_port': [12345, 12346, 53, 0, 54321],
        'dst_port': [80, 443, 53, 0, 22],
        'tcp_flags': [2, 2, 0, 0, 2],
        'payload_size': [50, 100, 150, 30, 70],
        'header_length': [50, 50, 50, 50, 50],
        'window_size': [65535, 65535, 0, 0, 65535],
        'time_delta': [0.1, 0.2, 0.15, 0.3, 0.25],
        'packet_rate': [10.0, 5.0, 6.7, 3.3, 4.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_model_data():
    """Create sample data for model training/testing."""
    X = np.random.rand(100, 10)  # 100 samples, 10 features
    y = np.random.randint(0, 2, 100)  # Binary labels
    return X, y


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary."""
    return {
        'capture': {
            'interface': 'eth0',
            'buffer_timeout': 1000,
            'snaplen': 65535,
            'promisc': True,
        },
        'alert': {
            'enabled': True,
            'console_enabled': True,
            'file_enabled': False,
            'email_enabled': False,
            'webhook_enabled': False,
        },
        'model': {
            'algorithm': 'isolation_forest',
            'contamination': 0.1,
            'n_estimators': 100,
        },
    }


@pytest.fixture
def email_config():
    """Create sample email configuration."""
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender': 'test@example.com',
        'password': 'test_password',
        'recipients': ['admin@example.com'],
        'use_tls': True,
    }


@pytest.fixture
def webhook_config():
    """Create sample webhook configuration."""
    return {
        'url': 'https://hooks.example.com/webhook',
        'method': 'POST',
        'headers': {'Content-Type': 'application/json'},
        'timeout': 10,
        'retry_attempts': 3,
        'retry_delay': 2,
    }


@pytest.fixture
def sample_alert():
    """Create sample alert data."""
    return {
        'timestamp': '2025-11-14T10:30:00Z',
        'severity': 'high',
        'message': 'Anomalous traffic detected',
        'source_ip': '192.168.1.100',
        'destination_ip': '10.0.0.1',
        'protocol': 'TCP',
        'port': 80,
        'anomaly_score': 0.95,
        'details': {
            'packet_count': 1000,
            'byte_count': 150000,
            'duration': 60,
        },
    }


@pytest.fixture
def trained_model_file(temp_dir, sample_model_data):
    """Create a trained model file for testing."""
    from models.unsupervised import IsolationForestDetector
    from utils.secure_pickle import safe_save

    X, _ = sample_model_data
    model = IsolationForestDetector(contamination=0.1)
    model.train(X)

    model_path = temp_dir / "test_model.pkl"
    safe_save(model, str(model_path))
    return model_path


@pytest.fixture
def mock_network_interface(monkeypatch):
    """Mock network interface for testing."""
    def mock_get_working_if():
        return "eth0"

    try:
        from scapy.arch import get_working_if
        monkeypatch.setattr("scapy.arch.get_working_if", mock_get_working_if)
    except ImportError:
        pass

    return "eth0"


@pytest.fixture
def capture_config_file(temp_dir):
    """Create a temporary capture configuration file."""
    import yaml

    config = {
        'interface': 'eth0',
        'buffer_timeout': 1000,
        'snaplen': 65535,
        'promisc': True,
        'filter': '',
    }

    config_path = temp_dir / "capture_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def alert_config_file(temp_dir):
    """Create a temporary alert configuration file."""
    import yaml

    config = {
        'enabled': True,
        'console_enabled': True,
        'file_enabled': False,
        'file_path': 'alerts.json',
        'email_enabled': False,
        'webhook_enabled': False,
    }

    config_path = temp_dir / "alert_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def model_config_file(temp_dir):
    """Create a temporary model configuration file."""
    import yaml

    config = {
        'isolation_forest': {
            'contamination': 0.1,
            'n_estimators': 100,
            'max_samples': 'auto',
            'random_state': 42,
        },
        'one_class_svm': {
            'kernel': 'rbf',
            'gamma': 'auto',
            'nu': 0.1,
        },
    }

    config_path = temp_dir / "model_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
    # Cleanup logic here if needed


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )
    config.addinivalue_line(
        "markers", "requires_root: marks tests that require root privileges"
    )
