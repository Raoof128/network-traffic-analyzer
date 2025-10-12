#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys

def test_imports():
    """Test all critical imports"""
    errors = []

    # Test capture module
    try:
        from capture import PacketSniffer, PcapHandler
        print("✓ Capture module imports OK")
    except Exception as e:
        errors.append(f"✗ Capture module: {e}")

    # Test features module
    try:
        from features import FeatureExtractor, FlowAggregator, FeaturePreprocessor
        print("✓ Features module imports OK")
    except Exception as e:
        errors.append(f"✗ Features module: {e}")

    # Test models module
    try:
        from models import IsolationForestDetector, RandomForestDetector, ModelEvaluator
        print("✓ Models module imports OK")
    except Exception as e:
        errors.append(f"✗ Models module: {e}")

    # Test detection module
    try:
        from detection import RealtimeDetector, AlertManager, AlertSeverity
        print("✓ Detection module imports OK")
    except Exception as e:
        errors.append(f"✗ Detection module: {e}")

    # Test visualization module
    try:
        from visualization import TrafficVisualizer, HTMLReportGenerator
        print("✓ Visualization module imports OK")
    except Exception as e:
        errors.append(f"✗ Visualization module: {e}")

    # Test config module
    try:
        from config import ConfigLoader
        print("✓ Config module imports OK")
    except Exception as e:
        errors.append(f"✗ Config module: {e}")

    # Test dependencies
    try:
        import scapy
        import pandas
        import numpy
        import sklearn
        import matplotlib
        import seaborn
        import yaml
        print("✓ All dependencies available")
    except Exception as e:
        errors.append(f"✗ Dependencies: {e}")

    if errors:
        print("\n❌ Import errors found:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
