#!/bin/bash
# Setup script for Network Traffic Analyzer

set -e  # Exit on error

echo "================================================"
echo "Network Traffic Analyzer - Setup Script"
echo "================================================"

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p logs
mkdir -p data/pcaps
mkdir -p data/datasets
mkdir -p models/trained_models
mkdir -p reports/templates
mkdir -p visualization/plots
echo "✓ Directories created"

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x analyzer.py train_model.py
echo "✓ Scripts are executable"

# Test imports
echo ""
echo "Testing imports..."
python test_imports.py

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the analyzer:"
echo "  sudo venv/bin/python analyzer.py --mode realtime --interface eth0"
echo ""
echo "To analyze a PCAP file:"
echo "  python analyzer.py --mode offline --pcap capture.pcap"
echo ""
