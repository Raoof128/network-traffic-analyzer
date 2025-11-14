# Frequently Asked Questions (FAQ)

## Table of Contents

- [General Questions](#general-questions)
- [Installation](#installation)
- [Usage](#usage)
- [Models and Training](#models-and-training)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Contributing](#contributing)

---

## General Questions

### What is Network Traffic Analyzer?

Network Traffic Analyzer is an ML-powered tool for detecting anomalies in network traffic. It supports both real-time analysis and offline PCAP file analysis using multiple machine learning algorithms.

### What makes this different from other network analysis tools?

- **ML-Powered Detection**: Uses advanced machine learning algorithms (Isolation Forest, One-Class SVM, etc.)
- **Multiple Detection Methods**: Supports both supervised and unsupervised learning
- **Enterprise Features**: Email alerts, webhook notifications, secure model loading
- **Modern API**: RESTful API with FastAPI and OpenAPI documentation
- **Production-Ready**: Docker support, comprehensive testing, professional CI/CD

### What are the system requirements?

**Minimum Requirements:**
- **OS**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk**: 500MB for installation, plus space for PCAP files and models

**For Real-time Capture:**
- Root/Administrator privileges (or CAP_NET_RAW capability on Linux)
- Network interface access

### Is this free and open source?

Yes! Network Traffic Analyzer is released under the **MIT License**, which means you can:
- Use it commercially
- Modify it
- Distribute it
- Use it privately

See [LICENSE](LICENSE) for full details.

---

## Installation

### How do I install the Network Traffic Analyzer?

**Method 1: From Source**
```bash
git clone https://github.com/Raoof128/network-traffic-analyzer.git
cd network-traffic-analyzer
pip install -r requirements.txt
```

**Method 2: Using pip (when available)**
```bash
pip install network-traffic-analyzer
```

**Method 3: Using Docker**
```bash
docker-compose up -d
```

### Do I need root privileges?

For **real-time packet capture**, yes. You need root/sudo for capturing packets from network interfaces.

For **offline PCAP analysis**, no root privileges are required.

**Linux Alternative** (avoid running as root):
```bash
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.x
```

### What dependencies are required?

**Core Dependencies:**
- scapy >= 2.5.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- matplotlib >= 3.7.0
- pyyaml >= 6.0

**Optional Dependencies:**
- FastAPI (for REST API)
- Docker (for containerized deployment)

See `requirements.txt` for the complete list.

### Why am I getting import errors?

**Common causes:**
1. **Missing dependencies**: Run `pip install -r requirements.txt`
2. **Wrong Python version**: Ensure you're using Python 3.8+
3. **Virtual environment not activated**: Activate your venv
4. **Conflicting installations**: Try a fresh virtual environment

---

## Usage

### How do I perform real-time traffic analysis?

```bash
sudo python analyzer.py --mode realtime --interface eth0 --model models/trained_models/isolation_forest.pkl
```

Replace `eth0` with your network interface name.

### How do I analyze a PCAP file?

```bash
python analyzer.py --mode offline --pcap captures/traffic.pcap --model models/trained_models/isolation_forest.pkl
```

### How do I list available network interfaces?

```bash
python analyzer.py --list-interfaces
```

### Can I filter specific traffic types?

Yes, use BPF filters:
```bash
# Capture only HTTP traffic
python analyzer.py --mode realtime --interface eth0 --filter "tcp port 80"

# Capture only DNS traffic
python analyzer.py --mode realtime --interface eth0 --filter "udp port 53"

# Capture traffic from specific IP
python analyzer.py --mode realtime --interface eth0 --filter "host 192.168.1.100"
```

### How do I set up email alerts?

1. Configure environment variables:
```bash
export NTA_EMAIL_PASSWORD="your_app_specific_password"
```

2. Edit `config/alert_config.yaml`:
```yaml
email_enabled: true
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender: "your_email@gmail.com"
  recipients:
    - "admin@example.com"
  use_tls: true
```

3. Run with alerts enabled:
```bash
python analyzer.py --mode realtime --interface eth0 --model models/model.pkl
```

### How do I use webhook notifications?

Edit `config/alert_config.yaml`:
```yaml
webhook_enabled: true
webhook:
  url: "https://hooks.example.com/webhook"
  method: "POST"
  timeout: 10
  retry_attempts: 3
```

---

## Models and Training

### Which ML algorithm should I use?

**Recommended for beginners:** Isolation Forest
- Fast training
- Good performance
- Works without labels (unsupervised)
- Default choice

**For labeled data:** Random Forest or Ensemble
- Better accuracy with labeled data
- Requires labeled training data

**For specific use cases:**
- **High accuracy needed**: Ensemble models
- **Fast detection**: Isolation Forest
- **Memory constrained**: One-Class SVM

### How do I train a new model?

```bash
# Unsupervised (no labels required)
python train_model.py --data datasets/traffic_features.csv --model-type isolation_forest --output models/my_model.pkl

# Supervised (requires labels)
python train_model.py --data datasets/labeled_traffic.csv --model-type random_forest --label-column "is_anomaly" --output models/my_model.pkl --evaluate
```

### What format should my training data be in?

Training data should be a **CSV file** with:
- One row per packet/flow
- Numerical features as columns
- Optional label column (for supervised learning)

**Example:**
```csv
packet_length,protocol_type,src_port,dst_port,is_anomaly
100,6,12345,80,0
150,6,12346,443,0
500,6,54321,22,1
```

### How do I improve model accuracy?

1. **Use more training data** (10,000+ samples recommended)
2. **Use labeled data** if available
3. **Try ensemble models** for better performance
4. **Tune hyperparameters** (contamination rate, n_estimators, etc.)
5. **Feature engineering** - add domain-specific features
6. **Cross-validation** - evaluate with `--evaluate` flag

### Can I use my own ML model?

Yes! As long as it implements `predict()` method and can be saved as a pickle file. Just ensure it's compatible with the feature extraction pipeline.

---

## Performance

### How fast is the analysis?

**Typical Performance:**
- **Real-time**: 10,000+ packets/second
- **Offline Analysis**: 100,000 packets in < 10 seconds
- **Detection Latency**: < 500ms

**Factors affecting performance:**
- Model complexity (Isolation Forest is fastest)
- Number of features
- Hardware specifications
- Network traffic volume

### How much memory does it use?

**Typical Memory Usage:**
- Base: ~500MB
- With model loaded: ~1GB
- Processing 100K packets: ~2GB
- Caching enabled: +200-500MB

### Can I analyze large PCAP files (>1GB)?

Yes, but you may need to:
1. **Increase available RAM**
2. **Use streaming mode** (process in chunks)
3. **Disable caching** for memory-constrained environments
4. **Filter traffic** to reduce load

### How can I improve performance?

1. **Enable caching**: Significantly speeds up repeated operations
2. **Use Isolation Forest**: Fastest model for real-time
3. **Reduce feature count**: Use only essential features
4. **Increase hardware**: More RAM and CPU cores help
5. **Use Docker**: Optimized container configuration

---

## Troubleshooting

### "Permission denied" error when capturing packets

**Cause**: Insufficient privileges for packet capture

**Solutions:**
1. Run with sudo: `sudo python analyzer.py ...`
2. Set capabilities (Linux):
   ```bash
   sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.x
   ```
3. Add user to appropriate group (varies by OS)

### "No module named 'scapy'" error

**Cause**: Scapy not installed

**Solution:**
```bash
pip install scapy>=2.5.0
```

### Model loading fails with "pickle.UnpicklingError"

**Cause**: Corrupted model file or version mismatch

**Solutions:**
1. Retrain the model with current version
2. Verify file integrity (not corrupted)
3. Check Python/library version compatibility
4. Ensure secure pickle is being used

### High false positive rate

**Solutions:**
1. **Retrain with representative data**: Ensure training data matches production traffic
2. **Adjust contamination rate**: Lower the contamination parameter
3. **Use more training data**: 10,000+ samples recommended
4. **Try different algorithms**: Ensemble models often have lower FP rates
5. **Tune thresholds**: Adjust anomaly score thresholds

### API server won't start

**Common issues:**
1. **Port already in use**: Change port with `--port 8001`
2. **FastAPI not installed**: `pip install fastapi uvicorn`
3. **Permission issues**: Don't need sudo for API server

**Start API:**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Out of memory errors

**Solutions:**
1. **Reduce batch size**: Process fewer packets at once
2. **Disable caching**: Set `--no-cache` flag
3. **Use simpler model**: Switch to Isolation Forest
4. **Increase system RAM**: Or use swap space
5. **Filter traffic**: Reduce traffic volume with BPF filters

---

## Security

### Is it safe to use pickle files?

We use **secure pickle loading** by default (v1.1.0+), which:
- Whitelists safe classes
- Blocks arbitrary code execution
- Optional HMAC verification

**Always:**
- Only load models from trusted sources
- Use `safe_load()` function
- Enable HMAC verification for sensitive deployments

### How should I secure my deployment?

**Best Practices:**
1. **Use HTTPS** for API in production
2. **Enable authentication** for API endpoints
3. **Rotate credentials** regularly
4. **Use environment variables** for secrets
5. **Enable firewall rules** appropriately
6. **Regular security updates**: Keep dependencies updated
7. **Monitor access logs**: Track API usage

### Can this detect all types of attacks?

**No.** This is an anomaly detection tool, not a comprehensive IDS/IPS. It:
- Detects **statistical anomalies** in traffic patterns
- Requires training data to learn "normal" behavior
- May miss sophisticated or slow attacks
- Should be used as **one layer** of security

**Not a replacement for:**
- Firewall
- IDS/IPS systems
- Endpoint protection
- Network segmentation

### Should I run this in production?

Yes, but with proper precautions:
- ✅ Thorough testing in your environment
- ✅ Proper training data
- ✅ Monitoring and alerting configured
- ✅ Regular model retraining
- ✅ Security hardening applied
- ✅ Backup and recovery plan

---

## Contributing

### How can I contribute?

See our [CONTRIBUTING.md](CONTRIBUTING.md) guide! We welcome:
- Code contributions
- Bug reports
- Documentation improvements
- Feature suggestions
- Testing and feedback

### I found a bug. What should I do?

1. **Check existing issues**: Might already be reported
2. **Create a bug report**: Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. **Include details**: OS, Python version, error messages, reproduction steps
4. **Provide logs**: Help us debug faster

### I have a feature idea. How do I suggest it?

1. **Check existing requests**: See if it's already suggested
2. **Create a feature request**: Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
3. **Describe the use case**: Why is this feature valuable?
4. **Discuss implementation**: Share your ideas

### How do I run the tests?

```bash
# All tests
make test

# Specific test file
pytest tests/test_features.py -v

# With coverage
make test-coverage
```

### Where can I get help?

1. **Check documentation**: README.md and docs/
2. **Search issues**: Might already be answered
3. **Create a question issue**: Use "question" label
4. **Check discussions**: GitHub Discussions tab

---

## Still Have Questions?

- **Documentation**: Check our [README.md](README.md)
- **Issues**: Browse [existing issues](https://github.com/Raoof128/network-traffic-analyzer/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/Raoof128/network-traffic-analyzer/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for security-related questions

---

**Last Updated**: November 2025
**Version**: 1.1.0
