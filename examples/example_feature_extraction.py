#!/usr/bin/env python3
"""
Example: Extract features from packets
Demonstrates packet and flow feature extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scapy.all import IP, TCP, UDP, Ether
from features import FeatureExtractor, FlowAggregator
import pandas as pd

def main():
    print("="*60)
    print("Network Traffic Analyzer - Feature Extraction Example")
    print("="*60)

    # Create sample packets
    print("\n1. Creating sample packets...")
    packets = [
        Ether() / IP(src="192.168.1.100", dst="8.8.8.8") / TCP(sport=50000, dport=443),
        Ether() / IP(src="192.168.1.100", dst="8.8.8.8") / TCP(sport=50000, dport=443),
        Ether() / IP(src="192.168.1.100", dst="8.8.8.8") / TCP(sport=50000, dport=443),
        Ether() / IP(src="192.168.1.101", dst="10.0.0.1") / UDP(sport=53, dport=5353),
        Ether() / IP(src="192.168.1.102", dst="1.1.1.1") / TCP(sport=60000, dport=80)
    ]
    print(f"   Created {len(packets)} sample packets")

    # Extract packet-level features
    print("\n2. Extracting packet-level features...")
    extractor = FeatureExtractor()
    packet_df = extractor.extract_batch_features(packets)

    print(f"   Extracted {len(packet_df)} packet features")
    print(f"   Features: {', '.join(packet_df.columns.tolist()[:5])}...")

    print("\n   Sample packet features:")
    print(packet_df[['src_ip', 'dst_ip', 'protocol', 'src_port', 'dst_port', 'packet_size']].head())

    # Extract flow-level features
    print("\n3. Extracting flow-level features...")
    aggregator = FlowAggregator()
    flow_df = aggregator.create_flow_features(packets)

    print(f"   Created {len(flow_df)} flows")
    print(f"   Flow features: {', '.join(flow_df.columns.tolist()[:5])}...")

    print("\n   Sample flow features:")
    if len(flow_df) > 0:
        print(flow_df[['flow_id', 'total_packets', 'total_bytes', 'flow_duration']].head())

    # Save to CSV
    print("\n4. Saving features to CSV...")
    packet_df.to_csv('data/datasets/example_packet_features.csv', index=False)
    flow_df.to_csv('data/datasets/example_flow_features.csv', index=False)
    print("   ✓ Saved to data/datasets/")

    print("\n" + "="*60)
    print("✅ Feature extraction complete!")
    print("="*60)

if __name__ == '__main__':
    main()
