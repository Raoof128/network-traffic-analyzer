# 🛡️ Network Traffic Analyzer with ML Anomaly Detection

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen.svg)](https://github.com/yourusername/network-traffic-analyzer)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688.svg)](https://fastapi.tiangolo.com/)

**Enterprise-grade network traffic analysis with ML-powered anomaly detection**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Documentation](#-documentation) • [API](#-rest-api) • [Docker](#-docker-deployment)

</div>

---

## 🌟 Overview

A comprehensive Python-based network traffic analyzer that combines **real-time packet capture**, **advanced feature extraction**, and **machine learning models** to detect network anomalies. Built with security, performance, and enterprise deployment in mind.

### ✨ What's New in v1.1.0

- 🎯 **Enterprise Alerting**: Email (SMTP) + Webhook notifications with retry logic
- 🔒 **Security Hardening**: Secure pickle loading prevents code injection attacks
- ✅ **Input Validation**: Comprehensive validation system for all inputs
- ⚡ **Performance Caching**: 10-100x speedup with LRU/TTL/Disk caching
- 🐳 **Docker Support**: Production-ready containerization with docker-compose
- 🌐 **REST API**: FastAPI with OpenAPI documentation
- 🛠️ **Dev Tools**: Pylint, Mypy, Flake8, Black, pre-commit hooks
- 📚 **Documentation**: Comprehensive guides and examples

## 🚀 Features

### Core Capabilities

- **📡 Real-time Packet Capture**: Live network traffic analysis from any interface
- **📁 Offline PCAP Analysis**: Analyze pre-captured pcap files
- **🤖 ML-Based Anomaly Detection**: 6 ML models including:
  - Isolation Forest (unsupervised)
  - One-Class SVM (unsupervised)
  - K-Means Clustering (unsupervised)
  - Random Forest (supervised)
  - SVM (supervised)
  - Ensemble Methods (supervised)
- **🎨 Visualization**: Interactive charts and HTML reports
- **💾 Low Resource Footprint**: Optimized for <2GB RAM

### Enterprise Features

- **📧 Multi-Channel Alerting**:
  - Console output with color-coded severity
  - File logging (JSON format)
  - Email alerts (SMTP with HTML templates)
  - Webhook notifications (HTTP POST/PUT with retry)

- **🔐 Security Hardening**:
  - Secure pickle loading with whitelist-based class restrictions
  - HMAC verification for model integrity
  - Comprehensive input validation
  - No hardcoded credentials

- **⚡ Performance Optimization**:
  - LRU cache for repeated operations
  - TTL cache for time-sensitive data
  - Disk cache for persistent storage
  - Thread-safe implementations

- **🐳 Docker Deployment**:
  - Multi-stage optimized builds
  - Docker Compose orchestration
  - Non-root containers
  - Volume persistence

- **🌐 REST API**:
  - 8 RESTful endpoints
  - OpenAPI/Swagger documentation
  - File upload support
  - Background task processing

- **🛠️ Development Tools**:
  - Code quality: Pylint, Mypy, Flake8
  - Formatting: Black, isort
  - Security: Bandit scanning
  - Pre-commit hooks
  - Makefile with 20+ commands

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Linux/macOS (recommended) or Windows with Npcap
- Root/sudo access (for packet capture)
- Docker (optional, for containerized deployment)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/Raoof128/network-traffic-analyzer.git
cd network-traffic-analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_improvements.py
```

### Development Install

```bash
# Install with development tools
pip install -r requirements-dev.txt

# Set up pre-commit hooks
make pre-commit-install

# Verify everything
make quality
```

## ⚡ Quick Start

### 1. Real-Time Analysis

```bash
# Basic real-time analysis
sudo python analyzer.py --mode realtime --interface eth0

# With trained model
sudo python analyzer.py --mode realtime \
  --interface eth0 \
  --model models/trained_models/isolation_forest.pkl

# With filters and duration
sudo python analyzer.py --mode realtime \
  --interface wlan0 \
  --filter "tcp port 80 or tcp port 443" \
  --duration 300
```

### 2. Offline PCAP Analysis

```bash
# Analyze PCAP file
python analyzer.py --mode offline \
  --pcap data/pcaps/traffic.pcap \
  --output reports/analysis.html

# With ML model
python analyzer.py --mode offline \
  --pcap data/pcaps/traffic.pcap \
  --model models/trained_models/isolation_forest.pkl \
  --output reports/detailed_report.html
```

### 3. Train ML Model

```bash
# Train Isolation Forest (unsupervised)
python train_model.py \
  --data data/datasets/network_traffic.csv \
  --model-type isolation_forest \
  --output models/trained_models/my_model.pkl

# Train Random Forest (supervised)
python train_model.py \
  --data data/datasets/labeled_traffic.csv \
  --model-type random_forest \
  --label-column attack \
  --evaluate
```

### 4. Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run analyzer service
docker-compose up analyzer

# Run with API
docker-compose --profile api up -d

# Access API docs
open http://localhost:8000/docs
```

### 5. Using REST API

```bash
# Start API server
uvicorn api.main:app --reload

# Upload and analyze PCAP
curl -X POST http://localhost:8000/api/v1/upload/pcap \
  -F "file=@traffic.pcap"

# Get analysis results
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"pcap_file": "data/pcaps/traffic.pcap"}'

# View interactive docs
open http://localhost:8000/docs
```

## 📧 Email & Webhook Alerts

### Configure Email Alerts

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your SMTP credentials
export NTA_EMAIL_PASSWORD="your_app_password"

# 3. Configure in config/alert_config.yaml
email:
  smtp_server: 'smtp.gmail.com'
  smtp_port: 587
  sender: 'alerts@example.com'
  recipients:
    - 'admin@example.com'
```

### Configure Webhook Alerts

```yaml
# config/alert_config.yaml
webhook:
  url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
  method: 'POST'
  timeout: 10
  retry_attempts: 3
```

### Using in Code

```python
from detection.alert_manager import AlertManager, AlertSeverity
import os

alert_mgr = AlertManager(
    email_config={
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'sender': 'alerts@example.com',
        'password': os.getenv('NTA_EMAIL_PASSWORD'),
        'recipients': ['admin@example.com']
    },
    webhook_config={
        'url': 'https://hooks.example.com/alerts',
        'method': 'POST'
    }
)

# Generate alert
alert_mgr.generate_alert(
    'port_scan',
    {'src_ip': '192.168.1.100', 'dst_ip': '10.0.0.1'},
    AlertSeverity.HIGH
)
```

## 🌐 REST API

The analyzer includes a full-featured REST API built with FastAPI.

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze` | Analyze PCAP file |
| GET | `/api/v1/analysis/{id}` | Get analysis results |
| GET | `/api/v1/models` | List available models |
| GET | `/api/v1/models/{name}` | Get model info |
| POST | `/api/v1/upload/pcap` | Upload PCAP file |
| GET | `/api/v1/stats` | System statistics |

### Python Client Example

```python
import requests

# Analyze PCAP
response = requests.post(
    'http://localhost:8000/api/v1/analyze',
    json={
        'pcap_file': 'data/pcaps/traffic.pcap',
        'model_path': 'models/trained_models/isolation_forest.pkl'
    }
)

result = response.json()
print(f"Anomalies: {result['anomaly_count']}/{result['total_flows']}")
print(f"Anomaly Rate: {result['anomaly_rate']:.2%}")
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Docker Deployment

### Quick Start

```bash
# Build image
docker build -t network-traffic-analyzer .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f analyzer
```

### Service Profiles

```bash
# Analyzer only
docker-compose up analyzer

# With API service
docker-compose --profile api up -d

# With dashboard (future feature)
docker-compose --profile dashboard up -d
```

### Environment Configuration

```bash
# Create .env file
cp .env.example .env

# Edit with your settings
INTERFACE=eth0
NTA_EMAIL_PASSWORD=your_password
API_PORT=8000
```

## 💻 Development

### Code Quality Tools

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# Security scan
make security

# Run all checks
make quality
```

### Testing

```bash
# Run all tests
make test

# With coverage
make test-coverage

# Fast tests only
make test-fast
```

### Pre-commit Hooks

```bash
# Install hooks
make pre-commit-install

# Run manually
make pre-commit-run
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Memory Usage | <2GB RAM (typical) |
| Packet Processing | 10,000+ packets/second |
| Real-time Latency | <500ms |
| Offline Analysis | 100K packets in <10 seconds |
| Cache Speedup | 10-100x for repeated operations |

## 🏗️ Architecture

```
network-traffic-analyzer/
├── analyzer.py                 # Main CLI entry point
├── train_model.py             # Model training script
├── requirements.txt           # Dependencies
├── Dockerfile                 # Container image
├── docker-compose.yml         # Service orchestration
├── Makefile                   # Development commands
│
├── api/                       # REST API
│   └── main.py               # FastAPI application
│
├── capture/                   # Packet capture
│   ├── packet_sniffer.py     # Real-time capture
│   └── pcap_handler.py       # PCAP operations
│
├── features/                  # Feature engineering
│   ├── extractor.py          # Feature extraction
│   └── preprocessor.py       # Normalization
│
├── models/                    # ML models
│   ├── unsupervised.py       # Unsupervised models
│   ├── supervised.py         # Supervised models
│   └── evaluator.py          # Model evaluation
│
├── detection/                 # Anomaly detection
│   ├── realtime_detector.py # Real-time detection
│   └── alert_manager.py      # Alert management
│
├── visualization/             # Reporting
│   ├── plots.py              # Chart generation
│   └── report_generator.py  # HTML reports
│
├── config/                    # Configuration
│   ├── alert_config.yaml     # Alert settings
│   └── capture_config.yaml   # Capture settings
│
├── utils/                     # Utilities (NEW)
│   ├── validators.py         # Input validation
│   ├── secure_pickle.py      # Secure loading
│   └── cache.py              # Performance caching
│
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## 📚 Documentation

- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Comprehensive guide to all improvements (784 lines)
- **[QUICKSTART_IMPROVEMENTS.md](QUICKSTART_IMPROVEMENTS.md)** - Quick start guide
- **[README_NEW_FEATURES.md](README_NEW_FEATURES.md)** - Feature highlights
- **[FINAL_CHECK_SUMMARY.md](FINAL_CHECK_SUMMARY.md)** - Complete audit trail
- **API Docs** - http://localhost:8000/docs (when API running)

## 🔧 Configuration

### Capture Configuration

Edit `config/capture_config.yaml`:

```yaml
network:
  interface: eth0
  promiscuous: true

capture:
  default_count: 1000
  timeout: 60
  max_stored_packets: 100000

filters:
  http: "tcp port 80 or tcp port 8080"
  https: "tcp port 443"
  dns: "udp port 53"
```

### Alert Configuration

Edit `config/alert_config.yaml`:

```yaml
alert_manager:
  channels:
    console: true
    file: true
    email: true
    webhook: true

email:
  smtp_server: 'smtp.gmail.com'
  smtp_port: 587
  sender: 'alerts@example.com'
  recipients:
    - 'admin@example.com'

webhook:
  url: 'https://hooks.example.com/alerts'
  method: 'POST'
  retry_attempts: 3
```

## 📖 Usage Examples

### Python API Examples

#### Secure Model Loading

```python
from models.unsupervised import IsolationForestDetector

# Models now use secure loading automatically
model = IsolationForestDetector.load('model.pkl')  # Secure by default!
```

#### Performance Caching

```python
from utils.cache import LRUCache, cached

cache = LRUCache(maxsize=1000)

@cached(cache=cache)
def expensive_operation(data):
    # Heavy computation here
    return result

# First call: computed
result = expensive_operation(data)

# Second call: from cache (instant!)
result = expensive_operation(data)
```

#### Input Validation

```python
from utils.validators import InputValidator, ValidationError

try:
    # Validate PCAP file
    path = InputValidator.validate_pcap_file('traffic.pcap')

    # Validate network interface
    iface = InputValidator.validate_network_interface('eth0')

    # Validate BPF filter
    filter_str = InputValidator.validate_bpf_filter('tcp port 80')

except ValidationError as e:
    print(f"Validation error: {e}")
```

## 🎯 Use Cases

- **Network Security Monitoring**: Detect anomalous traffic patterns
- **Intrusion Detection**: Identify potential security threats
- **Traffic Analysis**: Understand network behavior
- **Performance Monitoring**: Track network performance metrics
- **Forensics**: Analyze historical network traffic
- **Security Research**: Study network attack patterns

## 📊 Supported Datasets

### Recommended Training Datasets

- **[KDD Cup 99](http://kdd.ics.uci.edu/databases/kddcup99/)**: Classic intrusion detection dataset
- **[CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)**: Modern labeled dataset
- **[UNSW-NB15](https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-NB15-Datasets/)**: Contemporary network traffic
- **[CSE-CIC-IDS2018](https://www.unb.ca/cic/datasets/ids-2018.html)**: Recent comprehensive dataset

## 🐛 Troubleshooting

### Permission Denied

```bash
# Run with sudo for packet capture
sudo python analyzer.py --mode realtime --interface eth0
```

### Module Import Errors

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python verify_improvements.py
```

### Email Alerts Not Working

```bash
# Check SMTP credentials
echo $NTA_EMAIL_PASSWORD

# Use app-specific password for Gmail
# Enable "Less secure app access" or use OAuth2

# Test SMTP connection
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
```

### Docker Issues

```bash
# Check Docker is running
docker info

# Rebuild image
docker-compose build --no-cache

# View logs
docker-compose logs -f
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Install dev dependencies (`pip install -r requirements-dev.txt`)
4. Make your changes
5. Run quality checks (`make quality`)
6. Run tests (`make test`)
7. Commit your changes (`git commit -m 'Add AmazingFeature'`)
8. Push to the branch (`git push origin feature/AmazingFeature`)
9. Open a Pull Request

### Development Workflow

```bash
# Install development tools
make install-dev

# Make changes
# ... edit code ...

# Format and check
make format
make quality

# Test
make test

# Commit (pre-commit hooks run automatically)
git commit -m "Your message"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Scapy](https://scapy.net/)** - Packet manipulation
- **[scikit-learn](https://scikit-learn.org/)** - Machine learning algorithms
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework
- **[Matplotlib](https://matplotlib.org/)** & **[Seaborn](https://seaborn.pydata.org/)** - Visualization
- **[Docker](https://www.docker.com/)** - Containerization

## 📞 Support

- **Documentation**: See `IMPROVEMENTS.md` for detailed guides
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/Raoof128/network-traffic-analyzer/issues)
- **Discussions**: Join the conversation on [GitHub Discussions](https://github.com/Raoof128/network-traffic-analyzer/discussions)

## 🗺️ Roadmap

### Current Features (v1.1.0)
- ✅ Email & webhook alerts
- ✅ Secure pickle loading
- ✅ Input validation
- ✅ Performance caching
- ✅ Docker support
- ✅ REST API
- ✅ Development tools

### Planned Features (v1.2.0)
- 🔄 Real-time WebSocket dashboard
- 🔄 Extended protocol support (IPv6, DNS, TLS)
- 🔄 Kubernetes deployment manifests
- 🔄 API authentication (JWT)
- 🔄 PostgreSQL integration
- 🔄 Prometheus metrics

---

<div align="center">

**⚠️ Legal Notice**

This tool is for **defensive security and network monitoring purposes only**.
Always obtain proper authorization before monitoring network traffic.

**Made with ❤️ for the security community**

[⬆ Back to Top](#️-network-traffic-analyzer-with-ml-anomaly-detection)

</div>
