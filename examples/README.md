# Examples

This directory contains example scripts demonstrating various features of the Network Traffic Analyzer.

## Available Examples

### 1. Feature Extraction (`example_feature_extraction.py`)

Demonstrates how to extract features from packets and flows.

```bash
python examples/example_feature_extraction.py
```

**What it does:**
- Creates sample network packets
- Extracts packet-level features (IP, ports, protocols, sizes)
- Aggregates packets into flows
- Extracts flow-level features (duration, packet counts, statistics)
- Saves features to CSV files

**Output:**
- `data/datasets/example_packet_features.csv`
- `data/datasets/example_flow_features.csv`

### 2. Model Training (`example_model_training.py`)

Shows how to train an anomaly detection model.

```bash
python examples/example_model_training.py
```

**What it does:**
- Generates synthetic training data (normal + anomalous traffic)
- Preprocesses features (normalization, cleaning)
- Trains Isolation Forest model
- Tests predictions and shows anomaly scores
- Saves trained model and preprocessor

**Output:**
- `models/trained_models/example_model.pkl`
- `models/trained_models/example_preprocessor.pkl`

### 3. Generate Test PCAP (`example_generate_test_pcap.py`)

Creates a synthetic PCAP file for testing.

```bash
python examples/example_generate_test_pcap.py
```

**What it does:**
- Generates normal HTTP/HTTPS traffic
- Creates DNS queries
- Simulates anomalous patterns (port scans, large packets)
- Saves combined traffic to PCAP file

**Output:**
- `data/pcaps/test_traffic.pcap`

**To analyze the generated PCAP:**
```bash
python analyzer.py --mode offline --pcap data/pcaps/test_traffic.pcap
```

## Running Examples

### Prerequisites

Make sure you've set up the environment:

```bash
# Run setup script
./setup.sh

# Or manually:
source venv/bin/activate
pip install -r requirements.txt
```

### Run All Examples

```bash
# Feature extraction
python examples/example_feature_extraction.py

# Model training
python examples/example_model_training.py

# Generate test data
python examples/example_generate_test_pcap.py

# Analyze generated PCAP with trained model
python analyzer.py --mode offline \
  --pcap data/pcaps/test_traffic.pcap \
  --model models/trained_models/example_model.pkl \
  --preprocessor models/trained_models/example_preprocessor.pkl \
  --output reports/example_analysis.html
```

## Example Workflow

Complete workflow from data generation to analysis:

```bash
# 1. Generate test PCAP
python examples/example_generate_test_pcap.py

# 2. Extract features
python examples/example_feature_extraction.py

# 3. Train model
python examples/example_model_training.py

# 4. Analyze with trained model
python analyzer.py --mode offline \
  --pcap data/pcaps/test_traffic.pcap \
  --model models/trained_models/example_model.pkl \
  --output reports/test_analysis.html

# 5. View report
firefox reports/test_analysis.html
```

## Customization

Each example can be modified for your specific needs:

### Modify Feature Extraction

Edit `example_feature_extraction.py` to:
- Add custom packet patterns
- Extract additional features
- Change aggregation windows

### Adjust Model Training

Edit `example_model_training.py` to:
- Use different model types (OneClassSVM, KMeans)
- Adjust contamination rate
- Add more features

### Generate Custom Traffic

Edit `example_generate_test_pcap.py` to:
- Simulate specific attack patterns
- Create realistic traffic volumes
- Add custom protocols

## Troubleshooting

### Import Errors

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Denied

```bash
# Make scripts executable
chmod +x examples/*.py
```

### Missing Directories

```bash
# Create required directories
mkdir -p data/pcaps data/datasets models/trained_models reports
```

## Next Steps

After running the examples:

1. **Try Real Data**: Use your own PCAP files
2. **Train Custom Models**: Use real network data for training
3. **Tune Parameters**: Adjust detection thresholds and model parameters
4. **Real-Time Analysis**: Capture live traffic with `--mode realtime`

## Support

For questions or issues:
- Check main README.md
- Review documentation in docs/
- Open an issue on GitHub
