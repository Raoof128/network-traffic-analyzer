# Installation Guide

Complete installation guide for Network Traffic Analyzer on Linux systems.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Manual Installation](#manual-installation)
4. [Post-Installation](#post-installation)
5. [Troubleshooting](#troubleshooting)
6. [Platform-Specific Notes](#platform-specific-notes)

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 10+, CentOS 8+, Arch Linux)
- **Python**: 3.8 or higher
- **RAM**: 2GB (4GB recommended)
- **Disk Space**: 500MB
- **Network**: Root/sudo access for packet capture

### Recommended System
- **OS**: Ubuntu 22.04 LTS or Debian 12
- **Python**: 3.10+
- **RAM**: 8GB
- **Disk Space**: 2GB
- **CPU**: 2+ cores

### Dependencies
- Python 3.8+
- libpcap-dev
- python3-venv
- gcc/build-essential

---

## Quick Installation

### One-Line Install

```bash
cd /home/raouf/Desktop/Projects/nfa && ./setup.sh
```

This script will:
1. Check Python version
2. Create virtual environment
3. Install all dependencies
4. Create directory structure
5. Test imports

---

## Manual Installation

### Step 1: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libpcap-dev \
    build-essential
```

#### CentOS/RHEL/Fedora
```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-virtualenv \
    libpcap-devel \
    gcc \
    gcc-c++
```

#### Arch Linux
```bash
sudo pacman -S \
    python \
    python-pip \
    python-virtualenv \
    libpcap \
    base-devel
```

### Step 2: Clone/Navigate to Project

```bash
cd /home/raouf/Desktop/Projects/nfa
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

Your prompt should change to show `(venv)`.

### Step 5: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 6: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- scapy (packet manipulation)
- pandas, numpy (data processing)
- scikit-learn (machine learning)
- matplotlib, plotly, seaborn (visualization)
- pyyaml (configuration)
- pytest (testing)

### Step 7: Create Directory Structure

```bash
mkdir -p logs data/pcaps data/datasets models/trained_models reports visualization/plots
```

### Step 8: Make Scripts Executable

```bash
chmod +x analyzer.py train_model.py setup.sh test_imports.py
chmod +x examples/*.py
```

### Step 9: Test Installation

```bash
python test_imports.py
```

Expected output:
```
✓ Capture module imports OK
✓ Features module imports OK
✓ Models module imports OK
✓ Detection module imports OK
✓ Visualization module imports OK
✓ Config module imports OK
✓ All dependencies available

✅ All imports successful!
```

---

## Post-Installation

### Verify Packet Capture Capabilities

```bash
# Check interfaces
ip link show
# or
ifconfig

# Test capture (requires sudo)
sudo python3 -c "from scapy.all import sniff; print('Scapy capture OK')"
```

### Run Example Scripts

```bash
# Generate test data
python examples/example_generate_test_pcap.py

# Extract features
python examples/example_feature_extraction.py

# Train model
python examples/example_model_training.py
```

### First Analysis

```bash
# Analyze generated test PCAP
python analyzer.py --mode offline --pcap data/pcaps/test_traffic.pcap
```

---

## Troubleshooting

### Issue: "Permission denied" when capturing

**Solution:**
```bash
# Run with sudo
sudo venv/bin/python analyzer.py --mode realtime --interface eth0
```

### Issue: "ModuleNotFoundError: No module named 'scapy'"

**Cause:** Virtual environment not activated

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "error: externally-managed-environment"

**Cause:** Trying to install packages in system Python

**Solution:** Always use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Scapy can't find libpcap

**Ubuntu/Debian:**
```bash
sudo apt-get install libpcap-dev
pip install --force-reinstall scapy
```

**CentOS/RHEL:**
```bash
sudo dnf install libpcap-devel
pip install --force-reinstall scapy
```

### Issue: "No module named '_tkinter'"

**Solution:** Install tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo dnf install python3-tkinter
```

### Issue: Matplotlib backend errors

**Solution:** Use non-interactive backend:
```bash
export MPLBACKEND=Agg
python analyzer.py --mode offline --pcap capture.pcap
```

### Issue: Permission denied accessing /dev/bpf (macOS)

**Solution:**
```bash
sudo chmod o+r /dev/bpf*
```

---

## Platform-Specific Notes

### Ubuntu 20.04 / 22.04

Recommended platform. Everything should work out of the box.

```bash
# Install all dependencies
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv libpcap-dev build-essential

# Run setup
./setup.sh
```

### Debian 11 / 12

Similar to Ubuntu. May need to install `sudo` first:

```bash
su -
apt-get install sudo
usermod -aG sudo yourusername
exit
# Log out and back in
```

### CentOS Stream / Rocky Linux / AlmaLinux

Use `dnf` instead of `apt-get`:

```bash
sudo dnf install python3 python3-pip libpcap-devel gcc gcc-c++
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Arch Linux / Manjaro

```bash
sudo pacman -S python python-pip libpcap base-devel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows (WSL2)

Install WSL2 with Ubuntu:

```powershell
wsl --install
```

Then follow Ubuntu instructions inside WSL2.

### macOS

```bash
brew install python libpcap
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Verification Checklist

After installation, verify:

- [ ] Python 3.8+ installed: `python3 --version`
- [ ] Virtual environment created: `ls venv/`
- [ ] Dependencies installed: `pip list | grep scapy`
- [ ] Import test passes: `python test_imports.py`
- [ ] Directories created: `ls -d logs data models reports`
- [ ] Scripts executable: `ls -l analyzer.py`
- [ ] Can access network interface: `ip link show`

---

## Next Steps

After successful installation:

1. **Read Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
2. **Run Examples**: Try scripts in `examples/`
3. **Generate Test Data**: `python examples/example_generate_test_pcap.py`
4. **First Analysis**: Analyze test PCAP file
5. **Real-Time Capture**: Try live traffic analysis (requires sudo)

---

## Uninstallation

To completely remove the project:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf nfa

# Optional: Remove system dependencies
# Ubuntu/Debian
sudo apt-get remove libpcap-dev python3-venv
```

---

## Getting Help

- **Documentation**: Check README.md and docs/
- **Examples**: Review examples/ directory
- **Issues**: Report problems on GitHub
- **Community**: Join discussions

---

## Security Notes

- **Packet capture requires root**: Always use sudo for real-time capture
- **PCAP files contain sensitive data**: Handle with care
- **Virtual environment isolation**: Protects system Python
- **Keep dependencies updated**: Run `pip install --upgrade -r requirements.txt` regularly

---

## License

MIT License - See LICENSE file for details
