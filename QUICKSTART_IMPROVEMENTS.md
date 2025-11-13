# Quick Start Guide - New Features

This guide helps you quickly get started with the new improvements to the Network Traffic Analyzer.

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
# Install base requirements
pip install -r requirements.txt

# Optional: Install development tools
pip install -r requirements-dev.txt
```

### 2. Verify Installation
```bash
# Run verification script
python verify_improvements.py
```

## 📧 Email Alerts Setup

### Quick Configuration
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and set your email password
export NTA_EMAIL_PASSWORD="your_app_password_here"

# 3. Configure recipients in config/alert_config.yaml
# Edit the 'recipients' list under 'email' section
```

### Test Email Alerts
```python
from detection.alert_manager import AlertManager, AlertSeverity
import os

email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'sender': 'alerts@example.com',
    'password': os.getenv('NTA_EMAIL_PASSWORD'),
    'recipients': ['your-email@example.com']
}

alert_mgr = AlertManager(email_config=email_config)
alert_mgr.generate_alert(
    'test_alert',
    {'src_ip': '192.168.1.1', 'dst_ip': '10.0.0.1'},
    AlertSeverity.MEDIUM
)
```

## 🔐 Security Features

### Using Secure Pickle
All model loading now uses secure pickle by default. No code changes needed!

```python
# Old way (still works but not recommended)
# with open('model.pkl', 'rb') as f:
#     model = pickle.load(f)

# New way (automatic in all model classes)
from models.unsupervised import IsolationForestDetector
model = IsolationForestDetector.load('model.pkl')  # Secure by default!
```

### Input Validation
Validation is automatic in CLI. For programmatic use:

```python
from utils.validators import InputValidator, ValidationError

try:
    # Validate PCAP file
    path = InputValidator.validate_pcap_file('traffic.pcap')

    # Validate network interface
    iface = InputValidator.validate_network_interface('eth0')

except ValidationError as e:
    print(f"Validation error: {e}")
```

## ⚡ Performance Caching

### Quick Caching Example
```python
from utils.cache import LRUCache, cached

# Method 1: Direct cache usage
cache = LRUCache(maxsize=1000)
cache.put('key', 'value')
value = cache.get('key')

# Method 2: Decorator (recommended)
feature_cache = LRUCache(maxsize=500)

@cached(cache=feature_cache)
def extract_features(packet_data):
    # Expensive computation here
    return features

# Automatic caching!
features = extract_features(data)  # Computed
features = extract_features(data)  # From cache (fast!)
```

## 🐳 Docker Quick Start

### Run with Docker
```bash
# Build image
docker build -t network-traffic-analyzer .

# Run analyzer
docker run -it --rm --network host --cap-add=NET_ADMIN \
    -e INTERFACE=eth0 \
    network-traffic-analyzer \
    python analyzer.py --mode realtime --interface eth0

# OR use docker-compose
docker-compose up -d
```

### Run API Service
```bash
# Start API with docker-compose
docker-compose --profile api up -d

# Access API docs at http://localhost:8000/docs
```

## 🌐 REST API Quick Start

### Start API Server
```bash
# Option 1: Direct
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Docker
docker-compose --profile api up
```

### Quick API Test
```bash
# Health check
curl http://localhost:8000/health

# Upload and analyze PCAP
curl -X POST http://localhost:8000/api/v1/upload/pcap \
    -F "file=@traffic.pcap"

# Analyze uploaded file
curl -X POST http://localhost:8000/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"pcap_file": "data/pcaps/uploads/traffic.pcap"}'

# List models
curl http://localhost:8000/api/v1/models
```

### Python API Client
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
```

## 🛠️ Development Tools

### Using Makefile
```bash
# See all available commands
make help

# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# Security scan
make security

# Run all quality checks
make quality

# Run tests
make test
make test-coverage

# Install pre-commit hooks
make pre-commit-install
```

### Pre-commit Hooks
```bash
# Install hooks (runs checks before each commit)
make pre-commit-install

# Run manually on all files
make pre-commit-run

# Update hook versions
make pre-commit-update
```

## 📊 Common Workflows

### Workflow 1: Capture and Analyze
```bash
# 1. Capture traffic
sudo python analyzer.py --mode realtime --interface eth0 --duration 60

# 2. Train model on captured data
python train_model.py \
    --data data/datasets/training_data.csv \
    --model-type isolation_forest \
    --output models/my_model.pkl

# 3. Analyze offline with trained model
python analyzer.py \
    --mode offline \
    --pcap data/pcaps/capture.pcap \
    --model models/my_model.pkl \
    --output reports/analysis.html
```

### Workflow 2: API-based Analysis
```bash
# 1. Start API server
uvicorn api.main:app --reload &

# 2. Upload PCAP
curl -X POST http://localhost:8000/api/v1/upload/pcap \
    -F "file=@traffic.pcap"

# 3. Analyze
curl -X POST http://localhost:8000/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"pcap_file": "data/pcaps/uploads/traffic.pcap"}'
```

### Workflow 3: Development
```bash
# 1. Install dev tools
make install-dev

# 2. Make changes to code
# ... edit files ...

# 3. Format and check
make format
make quality

# 4. Run tests
make test

# 5. Commit (pre-commit hooks run automatically)
git add .
git commit -m "Your commit message"
```

## 🔍 Troubleshooting

### Email Alerts Not Working
1. Check SMTP credentials in `.env`
2. Use app-specific password for Gmail
3. Verify `config/alert_config.yaml` settings
4. Check firewall allows SMTP port (587/465)

### Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# For packet capture, ensure NET_ADMIN capability
docker run --cap-add=NET_ADMIN ...
```

### API Not Starting
```bash
# Check if FastAPI is installed
pip install fastapi uvicorn

# Check port is not in use
lsof -i :8000

# View logs
docker-compose logs api
```

### Import Errors
```bash
# Verify all dependencies installed
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Run verification script
python verify_improvements.py
```

## 📚 Next Steps

1. Read full documentation: `IMPROVEMENTS.md`
2. Explore API documentation: http://localhost:8000/docs
3. Review configuration files in `config/`
4. Check out example scripts in `examples/`
5. Join the community and contribute!

## 🆘 Getting Help

- Run verification: `python verify_improvements.py`
- Check documentation: `IMPROVEMENTS.md`
- View API docs: http://localhost:8000/docs
- See available make commands: `make help`

---

**Happy Analyzing! 🚀**
