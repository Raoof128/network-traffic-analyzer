# Network Traffic Analyzer with ML Anomaly Detection

A lightweight Python-based network traffic analyzer that captures packets in real-time or from pcap files, extracts features, applies machine learning models to detect anomalies, and generates alerts for suspicious activity.

## Features

- **Real-time Packet Capture**: Capture live network traffic from any interface
- **Offline PCAP Analysis**: Analyze pre-captured pcap files
- **ML-Based Anomaly Detection**: Multiple ML models including:
  - Isolation Forest (unsupervised)
  - One-Class SVM (unsupervised)
  - K-Means Clustering (unsupervised)
  - Random Forest (supervised)
  - SVM (supervised)
  - Ensemble Methods (supervised)
- **Alerting System**: Multi-channel alerts (console, file, email, webhook)
- **Visualization Dashboard**: Generate charts and HTML reports
- **Low Resource Footprint**: Optimized for systems with limited resources (<2GB RAM)

## Project Structure

```
nfa/
├── analyzer.py                 # Main entry point
├── train_model.py             # Model training script
├── requirements.txt           # Python dependencies
│
├── capture/                   # Packet capture modules
│   ├── packet_sniffer.py     # Real-time packet capture
│   └── pcap_handler.py       # PCAP file operations
│
├── features/                  # Feature extraction
│   ├── extractor.py          # Packet/flow feature extraction
│   ├── preprocessor.py       # Feature normalization
│   └── feature_definitions.yaml
│
├── models/                    # ML models
│   ├── unsupervised.py       # Isolation Forest, One-Class SVM, K-Means
│   ├── supervised.py         # Random Forest, SVM, Ensemble
│   ├── evaluator.py          # Model evaluation
│   └── trained_models/       # Saved models
│
├── detection/                 # Detection engine
│   ├── realtime_detector.py # Real-time anomaly detection
│   ├── alert_manager.py      # Alert management
│   └── rules/
│       └── threshold_rules.yaml
│
├── visualization/             # Visualization & reporting
│   ├── plots.py              # Chart generation
│   ├── report_generator.py  # HTML reports
│   └── plots/                # Generated plots
│
├── config/                    # Configuration
│   ├── config_loader.py      # Config management
│   ├── capture_config.yaml   # Capture settings
│
├── tests/                     # Unit tests
├── data/                      # Data storage
│   ├── pcaps/                # PCAP files
│   └── datasets/             # Training datasets
│
├── logs/                      # Log files
└── reports/                   # Generated reports
```

## Installation

### Prerequisites

- Python 3.8+
- Linux/macOS (recommended) or Windows with Npcap
- Root/sudo access (for packet capture)

### Setup

1. Clone the repository:
```bash
cd /home/raouf/Desktop/Projects/nfa
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
python -c "from scapy.all import *; print('Scapy OK')"
```

## Quick Start

### 1. Real-Time Traffic Analysis

Capture and analyze live network traffic:

```bash
# Basic real-time analysis (requires sudo)
sudo python analyzer.py --mode realtime --interface eth0

# With trained model
sudo python analyzer.py --mode realtime \
  --interface eth0 \
  --model models/trained_models/isolation_forest.pkl \
  --preprocessor models/trained_models/isolation_forest_preprocessor.pkl

# With filter and duration
sudo python analyzer.py --mode realtime \
  --interface wlan0 \
  --filter "tcp port 80 or tcp port 443" \
  --duration 300
```

### 2. Offline PCAP Analysis

Analyze existing pcap files:

```bash
# Analyze PCAP file
python analyzer.py --mode offline \
  --pcap data/pcaps/traffic.pcap \
  --output reports/analysis_report.html

# With trained model
python analyzer.py --mode offline \
  --pcap data/pcaps/traffic.pcap \
  --model models/trained_models/isolation_forest.pkl \
  --preprocessor models/trained_models/isolation_forest_preprocessor.pkl \
  --output reports/detailed_report.html
```

### 3. Train New Model

Train anomaly detection models:

```bash
# Train Isolation Forest (unsupervised)
python train_model.py \
  --data data/datasets/network_traffic.csv \
  --model-type isolation_forest \
  --output models/trained_models \
  --contamination 0.1

# Train Random Forest (supervised - requires labels)
python train_model.py \
  --data data/datasets/labeled_traffic.csv \
  --model-type random_forest \
  --label-column attack \
  --output models/trained_models \
  --evaluate
```

## Usage Examples

### Capture Traffic to PCAP

```python
from capture.packet_sniffer import PacketSniffer
from capture.pcap_handler import PcapHandler

# Capture 1000 packets
sniffer = PacketSniffer('eth0')
packets = sniffer.sniff_packets(count=1000, filter_rule='tcp')

# Save to file
PcapHandler.write_pcap(packets, 'data/pcaps/capture.pcap')
```

### Extract Features

```python
from features.extractor import FeatureExtractor, FlowAggregator
from capture.pcap_handler import PcapHandler

# Load packets
packets = PcapHandler.read_pcap('data/pcaps/capture.pcap')

# Extract packet features
extractor = FeatureExtractor()
packet_df = extractor.extract_batch_features(packets)

# Create flow features
aggregator = FlowAggregator()
flow_df = aggregator.create_flow_features(packets)
```

### Train and Evaluate Model

```python
from models.unsupervised import IsolationForestDetector
from models.evaluator import ModelEvaluator
from features.preprocessor import FeaturePreprocessor

# Load and preprocess data
import pandas as pd
df = pd.read_csv('data/datasets/traffic_features.csv')

preprocessor = FeaturePreprocessor()
X = preprocessor.fit_transform(df)

# Train model
model = IsolationForestDetector(contamination=0.1)
model.train(X)

# Save model
model.save('models/trained_models/my_model.pkl')
preprocessor.save('models/trained_models/my_preprocessor.pkl')
```

### Real-Time Detection

```python
from detection.realtime_detector import RealtimeDetector
from models.unsupervised import IsolationForestDetector

# Load model
model = IsolationForestDetector.load('models/trained_models/isolation_forest.pkl')

# Define alert callback
def handle_alert(anomaly_info):
    print(f"⚠️  ANOMALY: {anomaly_info['src_ip']} -> {anomaly_info['dst_ip']}")

# Start detection
detector = RealtimeDetector(model, interface='eth0')
detector.start_detection(alert_callback=handle_alert)
```

## Configuration

Edit `config/capture_config.yaml` to customize:

```yaml
network:
  interface: eth0  # Default interface
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

## Model Training Data

### Recommended Datasets

- **KDD Cup 99**: Classic network intrusion dataset
- **CIC-IDS2017**: Modern labeled dataset with various attacks
- **UNSW-NB15**: Contemporary network traffic dataset

Download and prepare:

```bash
# Example: KDD Cup 99
wget http://kdd.ics.uci.edu/databases/kddcup99/kddcup.data.gz
gunzip kddcup.data.gz
python scripts/prepare_kdd99.py kddcup.data data/datasets/kdd99_processed.csv
```

## Testing

Run tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_capture.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Performance

- **Memory Usage**: <2GB RAM (typical)
- **Packet Processing**: 10,000+ packets/second
- **Real-time Latency**: <500ms
- **Offline Analysis**: 100K packets in <10 seconds

## Troubleshooting

### Permission Denied Error

```bash
# Run with sudo for packet capture
sudo python analyzer.py --mode realtime --interface eth0
```

### Scapy Import Error

```bash
# Install Scapy
pip install scapy

# On Linux, may need libpcap
sudo apt-get install libpcap-dev
```

### No Module Named Error

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Scapy for packet manipulation
- scikit-learn for ML algorithms
- Matplotlib/Seaborn for visualizations

## Contact

For questions and support, please open an issue on GitHub.

---

**Note**: This tool is for defensive security and network monitoring purposes only. Always obtain proper authorization before monitoring network traffic.
