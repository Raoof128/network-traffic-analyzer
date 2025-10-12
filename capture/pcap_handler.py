"""
PCAP File Handler Module
Handles reading and writing pcap files using Scapy
"""

import logging
import os
from typing import List, Optional
from scapy.all import Packet, rdpcap, wrpcap, PcapReader
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PcapHandler:
    """Handle PCAP file operations"""

    @staticmethod
    def read_pcap(filename: str, count: Optional[int] = None) -> List[Packet]:
        """
        Read packets from a pcap file

        Args:
            filename: Path to pcap file
            count: Maximum number of packets to read (None = all)

        Returns:
            List of packets

        Raises:
            FileNotFoundError: If pcap file doesn't exist
            Exception: For other reading errors

        Example:
            >>> packets = PcapHandler.read_pcap('capture.pcap', count=1000)
            >>> print(f"Loaded {len(packets)} packets")
        """
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            raise FileNotFoundError(f"PCAP file not found: {filename}")

        try:
            logger.info(f"Reading pcap file: {filename}")
            read_count = count if count is not None else -1
            packets = rdpcap(filename, count=read_count)
            logger.info(f"Successfully loaded {len(packets)} packets from {filename}")
            return list(packets)

        except Exception as e:
            logger.error(f"Error reading pcap file {filename}: {e}")
            raise

    @staticmethod
    def read_pcap_streaming(filename: str):
        """
        Read pcap file as a stream (memory efficient for large files)

        Args:
            filename: Path to pcap file

        Yields:
            Packet objects one at a time

        Example:
            >>> for packet in PcapHandler.read_pcap_streaming('large_capture.pcap'):
            ...     process_packet(packet)
        """
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            raise FileNotFoundError(f"PCAP file not found: {filename}")

        try:
            logger.info(f"Streaming pcap file: {filename}")
            with PcapReader(filename) as pcap_reader:
                for packet in pcap_reader:
                    yield packet

        except Exception as e:
            logger.error(f"Error streaming pcap file {filename}: {e}")
            raise

    @staticmethod
    def write_pcap(packets: List[Packet], filename: str, append: bool = False):
        """
        Write packets to a pcap file

        Args:
            packets: List of packets to write
            filename: Output pcap file path
            append: If True, append to existing file

        Example:
            >>> PcapHandler.write_pcap(packets, 'output.pcap')
        """
        if not packets:
            logger.warning("No packets to write")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

            wrpcap(filename, packets, append=append)
            file_size = os.path.getsize(filename)
            logger.info(f"Successfully wrote {len(packets)} packets to {filename} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"Error writing pcap file {filename}: {e}")
            raise

    @staticmethod
    def write_pcap_auto(packets: List[Packet], output_dir: str = 'data/pcaps', prefix: str = 'capture') -> str:
        """
        Write packets to pcap file with automatic timestamp-based naming

        Args:
            packets: List of packets
            output_dir: Directory to save pcap file
            prefix: Filename prefix

        Returns:
            Path to created pcap file

        Example:
            >>> filepath = PcapHandler.write_pcap_auto(packets, prefix='attack')
            >>> # Creates: data/pcaps/attack_20231215_143022.pcap
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f"{prefix}_{timestamp}.pcap")

        PcapHandler.write_pcap(packets, filename)
        return filename

    @staticmethod
    def get_pcap_info(filename: str) -> dict:
        """
        Get information about a pcap file without loading all packets

        Args:
            filename: Path to pcap file

        Returns:
            Dictionary with pcap metadata

        Example:
            >>> info = PcapHandler.get_pcap_info('capture.pcap')
            >>> print(info['packet_count'], info['file_size'])
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"PCAP file not found: {filename}")

        try:
            # Get file stats
            file_size = os.path.getsize(filename)

            # Count packets efficiently
            packet_count = 0
            with PcapReader(filename) as pcap_reader:
                for _ in pcap_reader:
                    packet_count += 1

            info = {
                'filename': filename,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'packet_count': packet_count,
                'modified_time': datetime.fromtimestamp(os.path.getmtime(filename))
            }

            logger.info(f"PCAP info: {info}")
            return info

        except Exception as e:
            logger.error(f"Error getting pcap info: {e}")
            raise

    @staticmethod
    def filter_and_save(input_file: str, output_file: str, filter_func: callable):
        """
        Filter packets from input pcap and save to output pcap

        Args:
            input_file: Source pcap file
            output_file: Destination pcap file
            filter_func: Function that returns True to keep packet

        Example:
            >>> # Save only TCP packets
            >>> PcapHandler.filter_and_save(
            ...     'all_traffic.pcap',
            ...     'tcp_only.pcap',
            ...     lambda pkt: pkt.haslayer('TCP')
            ... )
        """
        filtered_packets = []

        for packet in PcapHandler.read_pcap_streaming(input_file):
            if filter_func(packet):
                filtered_packets.append(packet)

        PcapHandler.write_pcap(filtered_packets, output_file)
        logger.info(f"Filtered {len(filtered_packets)} packets from {input_file} to {output_file}")


# Convenience functions
def read_pcap(filename: str, count: Optional[int] = None) -> List[Packet]:
    """Convenience function to read pcap file"""
    return PcapHandler.read_pcap(filename, count)


def write_pcap(packets: List[Packet], filename: str, append: bool = False):
    """Convenience function to write pcap file"""
    PcapHandler.write_pcap(packets, filename, append)
