#!/usr/bin/env python3
"""
Example: Generate test PCAP file
Creates synthetic network traffic for testing
"""

from scapy.all import IP, TCP, UDP, ICMP, Ether, wrpcap
import random
import time

def generate_normal_traffic(count=100):
    """Generate normal HTTP/HTTPS traffic"""
    packets = []
    base_ip = "192.168.1"

    for i in range(count):
        src_ip = f"{base_ip}.{random.randint(100, 200)}"
        dst_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

        # HTTP or HTTPS
        dst_port = random.choice([80, 443, 8080])
        src_port = random.randint(49152, 65535)

        pkt = Ether() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port)
        packets.append(pkt)

    return packets


def generate_dns_traffic(count=50):
    """Generate DNS queries"""
    packets = []
    base_ip = "192.168.1"

    for i in range(count):
        src_ip = f"{base_ip}.{random.randint(100, 200)}"
        dst_ip = "8.8.8.8"  # Google DNS

        pkt = Ether() / IP(src=src_ip, dst=dst_ip) / UDP(sport=random.randint(49152, 65535), dport=53)
        packets.append(pkt)

    return packets


def generate_anomalous_traffic(count=20):
    """Generate suspicious traffic patterns"""
    packets = []
    attacker_ip = "10.0.0.50"

    # Port scan
    for port in range(1, count + 1):
        target_ip = "192.168.1.100"
        pkt = Ether() / IP(src=attacker_ip, dst=target_ip) / TCP(sport=random.randint(49152, 65535), dport=port, flags="S")
        packets.append(pkt)

    # Large packets (possible data exfiltration)
    for i in range(10):
        pkt = Ether() / IP(src=attacker_ip, dst="1.2.3.4") / TCP(sport=12345, dport=443) / ("X" * 1400)
        packets.append(pkt)

    return packets


def main():
    print("="*60)
    print("Network Traffic Analyzer - Generate Test PCAP")
    print("="*60)

    # Generate different types of traffic
    print("\n1. Generating normal HTTP/HTTPS traffic...")
    normal_packets = generate_normal_traffic(200)
    print(f"   Created {len(normal_packets)} normal packets")

    print("\n2. Generating DNS traffic...")
    dns_packets = generate_dns_traffic(50)
    print(f"   Created {len(dns_packets)} DNS packets")

    print("\n3. Generating anomalous traffic...")
    anomaly_packets = generate_anomalous_traffic(30)
    print(f"   Created {len(anomaly_packets)} anomalous packets")

    # Combine all packets
    all_packets = normal_packets + dns_packets + anomaly_packets
    random.shuffle(all_packets)

    print(f"\n4. Total packets: {len(all_packets)}")

    # Save to PCAP
    output_file = "data/pcaps/test_traffic.pcap"
    print(f"\n5. Saving to {output_file}...")
    wrpcap(output_file, all_packets)

    print("\n" + "="*60)
    print("✅ Test PCAP generated successfully!")
    print("="*60)
    print(f"\nFile: {output_file}")
    print(f"Total packets: {len(all_packets)}")
    print(f"  - Normal: {len(normal_packets) + len(dns_packets)}")
    print(f"  - Anomalous: {len(anomaly_packets)}")
    print("\nTo analyze:")
    print(f"  python analyzer.py --mode offline --pcap {output_file}")

if __name__ == '__main__':
    main()
