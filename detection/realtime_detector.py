"""
Real-Time Anomaly Detection Engine
Continuously analyze network traffic and detect anomalies
"""

import logging
import time
from typing import Optional, Callable, Dict, Any
from collections import deque
import pandas as pd
from scapy.all import Packet
import pickle

from capture.packet_sniffer import PacketSniffer
from features.extractor import FeatureExtractor, FlowAggregator
from features.preprocessor import FeaturePreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeDetector:
    """Real-time network anomaly detection"""

    def __init__(
        self,
        model,
        preprocessor: Optional[FeaturePreprocessor] = None,
        interface: Optional[str] = None,
        window_size: int = 30,
        buffer_size: int = 1000
    ):
        """
        Initialize real-time detector

        Args:
            model: Trained anomaly detection model
            preprocessor: Feature preprocessor (optional)
            interface: Network interface to monitor
            window_size: Time window for flow aggregation (seconds)
            buffer_size: Maximum packets to buffer

        Example:
            >>> detector = RealtimeDetector(model, preprocessor, interface='eth0')
            >>> detector.start_detection(alert_callback=handle_alert)
        """
        self.model = model
        self.preprocessor = preprocessor
        self.interface = interface
        self.window_size = window_size
        self.buffer_size = buffer_size

        self.sniffer = PacketSniffer(interface)
        self.flow_aggregator = FlowAggregator(flow_timeout=window_size)

        self.packet_buffer = deque(maxlen=buffer_size)
        self.anomaly_count = 0
        self.total_analyzed = 0
        self.running = False

        logger.info(f"Initialized RealtimeDetector on interface: {self.interface}")

    def analyze_packet_batch(
        self,
        packets: list,
        alert_callback: Optional[Callable] = None
    ):
        """
        Analyze a batch of packets for anomalies

        Args:
            packets: List of Scapy packets
            alert_callback: Function to call when anomaly detected
        """
        if not packets:
            return

        try:
            # Extract features
            packet_features = []
            for packet in packets:
                features = FeatureExtractor.extract_packet_features(packet)
                packet_features.append(features)

            # Convert to DataFrame
            df = pd.DataFrame(packet_features)

            # Filter out packets without IP info
            df = df[df['src_ip'].notna() & df['dst_ip'].notna()]

            if len(df) == 0:
                return

            # Select numeric features for ML
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            exclude_cols = ['timestamp']
            feature_cols = [c for c in numeric_cols if c not in exclude_cols]

            if not feature_cols:
                return

            X = df[feature_cols].fillna(0)

            # Preprocess if preprocessor available
            if self.preprocessor:
                try:
                    X = self.preprocessor.transform(X)
                except Exception as e:
                    logger.warning(f"Preprocessing error: {e}, using raw features")

            # Predict anomalies
            predictions = self.model.predict(X)

            # Process results
            anomaly_indices = [i for i, pred in enumerate(predictions) if pred == -1 or pred == 1]

            for idx in anomaly_indices:
                self.anomaly_count += 1
                anomaly_info = {
                    'timestamp': df.iloc[idx].get('timestamp', time.time()),
                    'src_ip': df.iloc[idx].get('src_ip'),
                    'dst_ip': df.iloc[idx].get('dst_ip'),
                    'src_port': df.iloc[idx].get('src_port'),
                    'dst_port': df.iloc[idx].get('dst_port'),
                    'protocol': df.iloc[idx].get('protocol'),
                    'packet_size': df.iloc[idx].get('packet_size'),
                    'prediction': predictions[idx],
                    'packet': packets[idx]
                }

                if alert_callback:
                    alert_callback(anomaly_info)

            self.total_analyzed += len(predictions)

        except Exception as e:
            logger.error(f"Error analyzing packet batch: {e}")

    def packet_callback(
        self,
        packet: Packet,
        alert_callback: Optional[Callable] = None
    ):
        """
        Callback for each captured packet

        Args:
            packet: Captured packet
            alert_callback: Alert callback function
        """
        self.packet_buffer.append(packet)

        # Analyze when buffer is full
        if len(self.packet_buffer) >= self.buffer_size:
            packets_to_analyze = list(self.packet_buffer)
            self.analyze_packet_batch(packets_to_analyze, alert_callback)
            self.packet_buffer.clear()

    def start_detection(
        self,
        alert_callback: Optional[Callable] = None,
        filter_rule: Optional[str] = None,
        duration: Optional[int] = None
    ):
        """
        Start real-time detection

        Args:
            alert_callback: Function to call when anomaly detected
            filter_rule: BPF filter rule
            duration: Detection duration in seconds (None = infinite)

        Example:
            >>> def handle_alert(anomaly):
            ...     print(f"Anomaly: {anomaly['src_ip']} -> {anomaly['dst_ip']}")
            >>> detector.start_detection(alert_callback=handle_alert)
        """
        logger.info(f"Starting real-time detection on {self.interface}...")
        logger.info(f"Filter: {filter_rule or 'None'}, Duration: {duration or 'Infinite'}")

        self.running = True
        start_time = time.time()

        try:
            def process_packet(packet):
                self.packet_callback(packet, alert_callback)

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    self.running = False
                    return True  # Stop filter

            self.sniffer.sniff_continuous(
                callback=process_packet,
                filter_rule=filter_rule,
                stop_filter=lambda p: not self.running
            )

        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        finally:
            # Analyze remaining packets in buffer
            if self.packet_buffer:
                self.analyze_packet_batch(list(self.packet_buffer), alert_callback)

            self.running = False
            logger.info(f"Detection complete. Analyzed: {self.total_analyzed}, Anomalies: {self.anomaly_count}")

    def stop_detection(self):
        """Stop real-time detection"""
        self.running = False
        logger.info("Stopping detection...")

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            'total_analyzed': self.total_analyzed,
            'anomaly_count': self.anomaly_count,
            'anomaly_rate': self.anomaly_count / self.total_analyzed if self.total_analyzed > 0 else 0,
            'buffer_size': len(self.packet_buffer)
        }


class ThresholdDetector:
    """Simple threshold-based anomaly detection"""

    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize threshold detector

        Args:
            rules: Detection rules dictionary

        Example:
            >>> rules = {
            ...     'max_packet_size': 1500,
            ...     'suspicious_ports': [22, 23, 3389],
            ...     'max_connections_per_ip': 100
            ... }
            >>> detector = ThresholdDetector(rules)
        """
        self.rules = rules
        self.ip_connection_count: Dict[str, int] = {}

    def check_packet(self, packet_features: Dict[str, Any]) -> bool:
        """
        Check if packet violates thresholds

        Args:
            packet_features: Packet features dictionary

        Returns:
            True if anomaly detected
        """
        # Check packet size
        if 'max_packet_size' in self.rules:
            if packet_features.get('packet_size', 0) > self.rules['max_packet_size']:
                logger.warning(f"Large packet detected: {packet_features['packet_size']} bytes")
                return True

        # Check suspicious ports
        if 'suspicious_ports' in self.rules:
            dst_port = packet_features.get('dst_port')
            if dst_port in self.rules['suspicious_ports']:
                logger.warning(f"Suspicious port detected: {dst_port}")
                return True

        # Check connection rate per IP
        if 'max_connections_per_ip' in self.rules:
            src_ip = packet_features.get('src_ip')
            if src_ip:
                self.ip_connection_count[src_ip] = self.ip_connection_count.get(src_ip, 0) + 1
                if self.ip_connection_count[src_ip] > self.rules['max_connections_per_ip']:
                    logger.warning(f"High connection rate from {src_ip}: {self.ip_connection_count[src_ip]}")
                    return True

        return False

    def reset_counters(self):
        """Reset connection counters"""
        self.ip_connection_count.clear()


def analyze_traffic_stream(
    interface: str,
    model,
    preprocessor: Optional[FeaturePreprocessor] = None,
    window_size: int = 30
):
    """
    Convenience function for real-time analysis

    Args:
        interface: Network interface
        model: Trained model
        preprocessor: Feature preprocessor
        window_size: Time window for aggregation
    """
    detector = RealtimeDetector(model, preprocessor, interface, window_size)

    def alert_handler(anomaly):
        logger.warning(f"⚠️  ANOMALY DETECTED: {anomaly['src_ip']}:{anomaly['src_port']} -> "
                      f"{anomaly['dst_ip']}:{anomaly['dst_port']} | Protocol: {anomaly['protocol']}")

    detector.start_detection(alert_callback=alert_handler)
