#!/usr/bin/env python3
"""
Installation Verification Script
Checks that everything is properly installed and configured
"""

import sys
import os
from pathlib import Path

def check_mark(condition, message):
    """Print check result"""
    if condition:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False

def main():
    print("="*70)
    print("Network Traffic Analyzer - Installation Verification")
    print("="*70)

    all_checks = []

    # 1. Python version
    print("\n📌 Checking Python Version...")
    import platform
    py_version = sys.version_info
    all_checks.append(check_mark(
        py_version >= (3, 8),
        f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro} (≥3.8 required)"
    ))

    # 2. Required modules
    print("\n📌 Checking Python Modules...")
    modules = [
        ('scapy', 'Scapy'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('sklearn', 'scikit-learn'),
        ('matplotlib', 'Matplotlib'),
        ('seaborn', 'Seaborn'),
        ('yaml', 'PyYAML'),
        ('pytest', 'Pytest')
    ]

    for module, name in modules:
        try:
            __import__(module)
            all_checks.append(check_mark(True, f"{name} installed"))
        except ImportError:
            all_checks.append(check_mark(False, f"{name} NOT installed"))

    # 3. Project structure
    print("\n📌 Checking Project Structure...")
    required_dirs = [
        'capture', 'features', 'models', 'detection', 'visualization',
        'config', 'tests', 'data', 'logs', 'reports', 'examples'
    ]

    for dirname in required_dirs:
        exists = Path(dirname).exists()
        all_checks.append(check_mark(exists, f"Directory: {dirname}/"))

    # 4. Required files
    print("\n📌 Checking Required Files...")
    required_files = [
        'analyzer.py',
        'train_model.py',
        'requirements.txt',
        'README.md',
        'setup.sh',
        'test_imports.py'
    ]

    for filename in required_files:
        exists = Path(filename).exists()
        all_checks.append(check_mark(exists, f"File: {filename}"))

    # 5. Module imports
    print("\n📌 Checking Module Imports...")
    imports = [
        ('capture', 'Capture module'),
        ('features', 'Features module'),
        ('models', 'Models module'),
        ('detection', 'Detection module'),
        ('visualization', 'Visualization module'),
        ('config', 'Config module')
    ]

    for module, name in imports:
        try:
            __import__(module)
            all_checks.append(check_mark(True, f"{name} imports"))
        except ImportError as e:
            all_checks.append(check_mark(False, f"{name} import error: {e}"))

    # 6. Configuration files
    print("\n📌 Checking Configuration Files...")
    config_files = [
        'config/capture_config.yaml',
        'config/model_config.yaml',
        'config/alert_config.yaml',
        'detection/rules/threshold_rules.yaml'
    ]

    for config_file in config_files:
        exists = Path(config_file).exists()
        all_checks.append(check_mark(exists, f"Config: {config_file}"))

    # 7. Example scripts
    print("\n📌 Checking Example Scripts...")
    example_scripts = [
        'examples/example_feature_extraction.py',
        'examples/example_model_training.py',
        'examples/example_generate_test_pcap.py'
    ]

    for script in example_scripts:
        exists = Path(script).exists() and os.access(script, os.X_OK)
        all_checks.append(check_mark(exists, f"Example: {script}"))

    # Summary
    print("\n" + "="*70)
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total) * 100

    if percentage == 100:
        print(f"🎉 PERFECT! All {total} checks passed!")
        print("\n✨ Installation is complete and verified!")
        print("\nNext steps:")
        print("  1. Read QUICKSTART.md for quick start guide")
        print("  2. Run: python examples/example_generate_test_pcap.py")
        print("  3. Run: python examples/example_model_training.py")
        print("  4. Try: python analyzer.py --mode offline --pcap data/pcaps/test_traffic.pcap")
        return_code = 0
    elif percentage >= 80:
        print(f"⚠️  {passed}/{total} checks passed ({percentage:.1f}%)")
        print("\nMost components are working. Review failed checks above.")
        return_code = 1
    else:
        print(f"❌ Only {passed}/{total} checks passed ({percentage:.1f}%)")
        print("\nInstallation incomplete. Please run: ./setup.sh")
        return_code = 1

    print("="*70)
    return return_code

if __name__ == '__main__':
    sys.exit(main())
