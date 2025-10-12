# Quick Start Guide

Get up and running with Network Traffic Analyzer in 5 minutes!

## 1. Installation (2 minutes)

```bash
# Navigate to project directory
cd /home/raouf/Desktop/Projects/nfa

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Quick Test (1 minute)

Test the installation:

```bash
# Check imports
python -c "from scapy.all import *; print('✓ Scapy OK')"
python -c "import sklearn; print('✓ scikit-learn OK')"
python -c "import pandas; print('✓ Pandas OK')"
```

## 3. First Capture (2 minutes)

### Option A: Analyze Sample PCAP (No sudo needed)

```bash
# Download sample PCAP
wget https://wiki.wireshark.org/uploads/__moin_import__/attachments/SampleCaptures/http.cap -O data/pcaps/sample.cap

# Analyze it
python analyzer.py --mode offline --pcap data/pcaps/sample.cap --output reports/my_first_report.html

# View report
firefox reports/my_first_report.html  # or your browser
```

### Option B: Live Capture (Requires sudo)

```bash
# Capture 100 packets from your network
sudo python analyzer.py --mode realtime --interface eth0 --duration 10

# Check logs
tail -f logs/alerts.log
```

## 4. Train Your First Model (Optional)

If you have labeled data:

```bash
# Train Isolation Forest
python train_model.py \
  --data data/datasets/your_data.csv \
  --model-type isolation_forest \
  --output models/trained_models
```

## Common Use Cases

### Use Case 1: Monitor HTTP Traffic

```bash
sudo python analyzer.py --mode realtime \
  --interface eth0 \
  --filter "tcp port 80 or tcp port 443" \
  --duration 60
```

### Use Case 2: Detect Port Scans

```bash
python analyzer.py --mode offline \
  --pcap suspicious_traffic.pcap \
  --model models/trained_models/isolation_forest.pkl \
  --output reports/port_scan_analysis.html
```

### Use Case 3: Analyze Network Baseline

```bash
# Capture normal traffic
sudo python analyzer.py --mode realtime \
  --interface eth0 \
  --duration 300

# Train model on normal traffic
python train_model.py \
  --data logs/traffic_features.csv \
  --model-type isolation_forest
```

## Troubleshooting

### "Permission denied" error
```bash
# Run with sudo for packet capture
sudo python analyzer.py --mode realtime --interface eth0
```

### "No module named 'scapy'"
```bash
# Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### "Interface not found"
```bash
# List available interfaces
ip link show
# or
ifconfig
```

## Next Steps

1. Read the full [README.md](README.md)
2. Explore example datasets in `data/datasets/`
3. Customize detection rules in `detection/rules/threshold_rules.yaml`
4. Train custom models with your data

## Support

- Issues: Open a GitHub issue
- Documentation: See `docs/` folder
- Examples: See `README.md` Usage section

---

**Happy Analyzing! 🛡️**
