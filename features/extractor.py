"""
Feature Extraction Module
Extract features from network packets and flows
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from scapy.all import Packet, IP, IPv6, TCP, UDP, ICMP
from collections import defaultdict
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract features from network packets"""

    @staticmethod
    def extract_packet_features(packet: Packet) -> Dict[str, Any]:
        """
        Extract features from a single packet

        Args:
            packet: Scapy packet object

        Returns:
            Dictionary of packet features

        Example:
            >>> features = FeatureExtractor.extract_packet_features(packet)
            >>> print(features['protocol'], features['packet_size'])
        """
        features = {
            'timestamp': float(packet.time) if hasattr(packet, 'time') else 0.0,
            'protocol': None,
            'ip_version': None,
            'src_ip': None,
            'dst_ip': None,
            'src_port': None,
            'dst_port': None,
            'packet_size': len(packet),
            'header_size': 0,
            'payload_size': 0,
            'tcp_flags': None,
            'tcp_window_size': None,
        }

        # IP layer features
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            features['ip_version'] = 4
            features['src_ip'] = ip_layer.src
            features['dst_ip'] = ip_layer.dst
            features['protocol'] = ip_layer.proto
            ihl = getattr(ip_layer, 'ihl', None)
            features['header_size'] = (ihl * 4) if ihl else 20

        elif packet.haslayer(IPv6):
            ipv6_layer = packet[IPv6]
            features['ip_version'] = 6
            features['src_ip'] = ipv6_layer.src
            features['dst_ip'] = ipv6_layer.dst
            features['protocol'] = ipv6_layer.nh
            features['header_size'] = 40  # IPv6 fixed header size

        # TCP layer features
        if packet.haslayer(TCP):
            tcp_layer = packet[TCP]
            features['src_port'] = tcp_layer.sport
            features['dst_port'] = tcp_layer.dport
            features['protocol'] = 'TCP'
            features['tcp_window_size'] = tcp_layer.window

            # Extract TCP flags
            flags = []
            if tcp_layer.flags.S: flags.append('SYN')
            if tcp_layer.flags.A: flags.append('ACK')
            if tcp_layer.flags.F: flags.append('FIN')
            if tcp_layer.flags.R: flags.append('RST')
            if tcp_layer.flags.P: flags.append('PSH')
            if tcp_layer.flags.U: flags.append('URG')
            features['tcp_flags'] = '|'.join(flags) if flags else None

            data_offset = getattr(tcp_layer, 'dataofs', None)
            features['header_size'] += (data_offset * 4) if data_offset else 20

        # UDP layer features
        elif packet.haslayer(UDP):
            udp_layer = packet[UDP]
            features['src_port'] = udp_layer.sport
            features['dst_port'] = udp_layer.dport
            features['protocol'] = 'UDP'
            features['header_size'] += 8  # UDP header size

        # ICMP
        elif packet.haslayer(ICMP):
            features['protocol'] = 'ICMP'

        # Calculate payload size
        features['payload_size'] = max(features['packet_size'] - features['header_size'], 0)

        return features

    @staticmethod
    def extract_batch_features(packets: List[Packet]) -> pd.DataFrame:
        """
        Extract features from multiple packets

        Args:
            packets: List of Scapy packet objects

        Returns:
            DataFrame with packet features

        Example:
            >>> df = FeatureExtractor.extract_batch_features(packets)
            >>> print(df.shape, df.columns.tolist())
        """
        features_list = []

        for packet in packets:
            try:
                features = FeatureExtractor.extract_packet_features(packet)
                features_list.append(features)
            except Exception as e:
                logger.warning(f"Error extracting features from packet: {e}")
                continue

        df = pd.DataFrame(features_list)
        logger.info(f"Extracted features from {len(df)} packets")

        return df


class FlowAggregator:
    """Aggregate packets into flows and extract flow-level features"""

    def __init__(self, flow_timeout: int = 120):
        """
        Initialize flow aggregator

        Args:
            flow_timeout: Timeout for inactive flows (seconds)
        """
        self.flow_timeout = flow_timeout
        self.flows: Dict[str, List[Dict]] = defaultdict(list)

    @staticmethod
    def create_flow_id(src_ip: str, src_port: int, dst_ip: str, dst_port: int, protocol: str) -> str:
        """Create unique flow identifier"""
        return f"{src_ip}:{src_port}->{dst_ip}:{dst_port}:{protocol}"

    def add_packet_to_flow(self, packet_features: Dict[str, Any]):
        """Add packet to appropriate flow"""
        src_ip = packet_features.get('src_ip')
        dst_ip = packet_features.get('dst_ip')
        src_port = packet_features.get('src_port', 0)
        dst_port = packet_features.get('dst_port', 0)
        protocol = packet_features.get('protocol', 'UNKNOWN')

        if not src_ip or not dst_ip:
            return

        flow_id = self.create_flow_id(src_ip, src_port, dst_ip, dst_port, protocol)
        self.flows[flow_id].append(packet_features)

    def extract_flow_features(self, flow_id: str, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract aggregated features from a flow

        Args:
            flow_id: Flow identifier
            packets: List of packet feature dictionaries

        Returns:
            Dictionary of flow features
        """
        if not packets:
            return {}

        timestamps = [p['timestamp'] for p in packets if p.get('timestamp')]
        packet_sizes = [p['packet_size'] for p in packets if p.get('packet_size')]

        # Flow identification
        first_packet = packets[0]
        features = {
            'flow_id': flow_id,
            'src_ip': first_packet.get('src_ip'),
            'dst_ip': first_packet.get('dst_ip'),
            'src_port': first_packet.get('src_port'),
            'dst_port': first_packet.get('dst_port'),
            'protocol': first_packet.get('protocol'),
        }

        # Duration
        if len(timestamps) > 1:
            features['flow_duration'] = max(timestamps) - min(timestamps)
            features['start_time'] = min(timestamps)
            features['end_time'] = max(timestamps)
        else:
            features['flow_duration'] = 0
            features['start_time'] = timestamps[0] if timestamps else 0
            features['end_time'] = timestamps[0] if timestamps else 0

        # Packet counts
        features['total_packets'] = len(packets)

        # Bytes
        features['total_bytes'] = sum(packet_sizes)

        # Statistics
        if packet_sizes:
            features['avg_packet_size'] = np.mean(packet_sizes)
            features['std_packet_size'] = np.std(packet_sizes)
            features['min_packet_size'] = np.min(packet_sizes)
            features['max_packet_size'] = np.max(packet_sizes)
        else:
            features['avg_packet_size'] = 0
            features['std_packet_size'] = 0
            features['min_packet_size'] = 0
            features['max_packet_size'] = 0

        # Rates
        if features['flow_duration'] > 0:
            features['packets_per_second'] = features['total_packets'] / features['flow_duration']
            features['bytes_per_second'] = features['total_bytes'] / features['flow_duration']
        else:
            features['packets_per_second'] = 0
            features['bytes_per_second'] = 0

        # Inter-arrival time
        if len(timestamps) > 1:
            iats = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            iats_ms = [iat * 1000 for iat in iats]  # Convert to milliseconds
            features['avg_iat'] = np.mean(iats_ms)
            features['std_iat'] = np.std(iats_ms)
        else:
            features['avg_iat'] = 0
            features['std_iat'] = 0

        # TCP flag counts
        features['syn_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'SYN' in p['tcp_flags'])
        features['ack_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'ACK' in p['tcp_flags'])
        features['fin_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'FIN' in p['tcp_flags'])
        features['rst_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'RST' in p['tcp_flags'])
        features['psh_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'PSH' in p['tcp_flags'])
        features['urg_count'] = sum(1 for p in packets if p.get('tcp_flags') and 'URG' in p['tcp_flags'])

        return features

    def create_flow_features(self, packets: List[Packet]) -> pd.DataFrame:
        """
        Create flow features from packets

        Args:
            packets: List of Scapy packets

        Returns:
            DataFrame with flow features

        Example:
            >>> aggregator = FlowAggregator()
            >>> flow_df = aggregator.create_flow_features(packets)
        """
        # First extract packet features
        for packet in packets:
            try:
                packet_features = FeatureExtractor.extract_packet_features(packet)
                self.add_packet_to_flow(packet_features)
            except Exception as e:
                logger.warning(f"Error processing packet: {e}")
                continue

        # Then create flow features
        flow_features_list = []
        for flow_id, flow_packets in self.flows.items():
            flow_features = self.extract_flow_features(flow_id, flow_packets)
            if flow_features:
                flow_features_list.append(flow_features)

        df = pd.DataFrame(flow_features_list)
        logger.info(f"Created {len(df)} flows from {len(packets)} packets")

        return df

    def clear_flows(self):
        """Clear all stored flows"""
        count = len(self.flows)
        self.flows.clear()
        logger.info(f"Cleared {count} flows from memory")


def extract_packet_features(packet: Packet) -> Dict[str, Any]:
    """Convenience function for packet feature extraction"""
    return FeatureExtractor.extract_packet_features(packet)


def create_flow_features(packets: List[Packet], window_size: int = 30) -> pd.DataFrame:
    """Convenience function for flow feature extraction"""
    aggregator = FlowAggregator(flow_timeout=window_size)
    return aggregator.create_flow_features(packets)
