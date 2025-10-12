#!/usr/bin/env python3
"""
Example: Train anomaly detection model
Demonstrates unsupervised model training
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from features import FeaturePreprocessor
from models import IsolationForestDetector, ModelEvaluator

def main():
    print("="*60)
    print("Network Traffic Analyzer - Model Training Example")
    print("="*60)

    # Generate synthetic training data
    print("\n1. Generating synthetic training data...")
    np.random.seed(42)

    # Normal traffic patterns
    normal_data = pd.DataFrame({
        'packet_size': np.random.normal(500, 100, 800),
        'bytes_per_second': np.random.normal(1000, 200, 800),
        'packets_per_second': np.random.normal(10, 2, 800),
        'avg_iat': np.random.normal(100, 20, 800),
        'total_packets': np.random.randint(5, 50, 800)
    })

    # Anomalous traffic patterns (larger, faster, more packets)
    anomaly_data = pd.DataFrame({
        'packet_size': np.random.normal(1400, 200, 200),
        'bytes_per_second': np.random.normal(5000, 1000, 200),
        'packets_per_second': np.random.normal(50, 10, 200),
        'avg_iat': np.random.normal(20, 5, 200),
        'total_packets': np.random.randint(100, 500, 200)
    })

    # Combine data
    X_train = pd.concat([normal_data, anomaly_data], ignore_index=True)
    print(f"   Generated {len(X_train)} training samples")

    # Preprocess features
    print("\n2. Preprocessing features...")
    preprocessor = FeaturePreprocessor(normalization='standard')
    X_train_processed = preprocessor.fit_transform(X_train)
    print(f"   Preprocessed {len(X_train_processed)} samples")
    print(f"   Features: {X_train_processed.columns.tolist()}")

    # Train Isolation Forest
    print("\n3. Training Isolation Forest model...")
    model = IsolationForestDetector(
        contamination=0.2,  # Expect 20% anomalies
        n_estimators=100,
        random_state=42
    )
    model.train(X_train_processed)
    print(f"   ✓ Model trained in {model.training_time:.2f} seconds")

    # Test predictions
    print("\n4. Testing predictions...")
    predictions = model.predict(X_train_processed)

    anomaly_count = np.sum(predictions == -1)
    normal_count = np.sum(predictions == 1)

    print(f"   Detected {anomaly_count} anomalies ({anomaly_count/len(predictions)*100:.1f}%)")
    print(f"   Detected {normal_count} normal samples ({normal_count/len(predictions)*100:.1f}%)")

    # Get anomaly scores
    scores = model.predict_proba(X_train_processed)
    print(f"\n   Anomaly score range: {scores.min():.3f} to {scores.max():.3f}")

    # Save model
    print("\n5. Saving model...")
    model.save('models/trained_models/example_model.pkl')
    preprocessor.save('models/trained_models/example_preprocessor.pkl')
    print("   ✓ Model saved to models/trained_models/")

    print("\n" + "="*60)
    print("✅ Model training complete!")
    print("="*60)
    print("\nTo use this model:")
    print("  python analyzer.py --mode offline \\")
    print("    --pcap capture.pcap \\")
    print("    --model models/trained_models/example_model.pkl \\")
    print("    --preprocessor models/trained_models/example_preprocessor.pkl")

if __name__ == '__main__':
    main()
