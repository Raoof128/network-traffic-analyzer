"""
Packet Sniffer Module
Handles real-time packet capture from network interfaces using Scapy
"""

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional

from scapy.all import Packet, conf, get_if_list, sniff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PacketSniffer:
    """Real-time packet capture from network interfaces"""

    LOOPBACK_NAMES = {"lo", "lo0", "loopback"}
    LOOPBACK_PREFIXES = ("lo",)
    WIRED_PREFIXES = ("eth", "en", "eno", "ens", "enp", "enx")
    WIRELESS_PREFIXES = ("wlan", "wl", "wwan")
    VIRTUAL_PREFIXES = ("docker", "veth", "virbr", "vmnet", "br", "tap", "tun", "podman", "kube", "vbox")

    def __init__(self, interface: Optional[str] = None):
        """
        Initialize packet sniffer

        Args:
            interface: Network interface to capture from (e.g., 'eth0', 'wlan0')
                      If None, uses detected default interface
        """
        self.interface = self.resolve_interface(interface)
        self.packets: List[Packet] = []
        self.capture_running = False
        logger.info("Initialized PacketSniffer on interface: %s", self.interface)

    def sniff_packets(
        self,
        count: int = 0,
        timeout: Optional[int] = None,
        filter_rule: Optional[str] = None,
        prn: Optional[Callable] = None,
        store: bool = True
    ) -> List[Packet]:
        """
        Capture packets from network interface

        Args:
            count: Number of packets to capture (0 = infinite)
            timeout: Stop capture after timeout seconds
            filter_rule: BPF filter (e.g., 'tcp port 80', 'udp', 'icmp')
            prn: Callback function to call for each packet
            store: Whether to store packets in memory

        Returns:
            List of captured packets

        Example:
            >>> sniffer = PacketSniffer('eth0')
            >>> packets = sniffer.sniff_packets(count=100, filter_rule='tcp')
        """
        try:
            logger.info("Starting packet capture on %s", self.interface)
            logger.info(
                "Filter: %s, Count: %s, Timeout: %s",
                filter_rule or "None",
                count,
                timeout
            )

            self.capture_running = True
            start_time = time.time()

            packets = sniff(
                iface=self.interface,
                count=count,
                timeout=timeout,
                filter=filter_rule,
                prn=prn,
                store=store
            )

            self.capture_running = False
            elapsed = time.time() - start_time

            if store:
                self.packets.extend(packets)

            logger.info("Captured %d packets in %.2f seconds", len(packets), elapsed)
            return list(packets)

        except PermissionError:
            logger.error("Permission denied: Run with sudo/root privileges")
            raise
        except Exception as exc:
            logger.error("Error capturing packets: %s", exc)
            self.capture_running = False
            raise

    def sniff_continuous(
        self,
        callback: Callable[[Packet], None],
        filter_rule: Optional[str] = None,
        stop_filter: Optional[Callable[[Packet], bool]] = None
    ):
        """
        Continuously capture packets with callback processing

        Args:
            callback: Function to process each packet
            filter_rule: BPF filter
            stop_filter: Function that returns True to stop capture
        """
        try:
            logger.info("Starting continuous capture on %s", self.interface)
            self.capture_running = True

            sniff(
                iface=self.interface,
                prn=callback,
                filter=filter_rule,
                stop_filter=stop_filter,
                store=False
            )

        except KeyboardInterrupt:
            logger.info("Capture stopped by user")
        except Exception as exc:
            logger.error("Error in continuous capture: %s", exc)
            raise
        finally:
            self.capture_running = False

    @staticmethod
    def resolve_interface(requested: Optional[str]) -> str:
        """
        Resolve the network interface to use for capture.

        Args:
            requested: Preferred interface name, or None to auto-detect.

        Returns:
            Name of the interface that will be used.

        Raises:
            ValueError: If no suitable interface can be found.
        """
        available_interfaces = PacketSniffer.get_available_interfaces()

        if requested:
            matched = PacketSniffer._match_interface(requested, available_interfaces)
            if matched:
                return matched
            logger.warning(
                "Interface '%s' not found. Attempting automatic selection.",
                requested
            )

        if not available_interfaces:
            raise ValueError("No network interfaces detected. Check your system configuration.")

        default_iface = getattr(conf, "iface", None)
        matched_default = (
            PacketSniffer._match_interface(default_iface, available_interfaces)
            if default_iface
            else None
        )

        if matched_default:
            if (
                not PacketSniffer._is_loopback(matched_default)
                or len(available_interfaces) == 1
            ):
                logger.info("Using default Scapy interface: %s", matched_default)
                return matched_default

        for iface in available_interfaces:
            if not PacketSniffer._is_loopback(iface):
                logger.info("Auto-selected interface: %s", iface)
                return iface

        fallback_interface = available_interfaces[0]
        logger.info("Only loopback interfaces detected. Using %s", fallback_interface)
        return fallback_interface

    @staticmethod
    def get_available_interfaces() -> List[str]:
        """
        Get prioritized list of available network interfaces.

        Returns:
            List of interface names ordered by preference.
        """
        interfaces: List[str] = []

        try:
            interfaces = get_if_list()
        except PermissionError as exc:
            logger.warning("Permission error listing interfaces via Scapy: %s", exc)
        except Exception as exc:
            logger.warning("Error getting interfaces via Scapy: %s", exc)

        if not interfaces:
            sysfs_path = Path("/sys/class/net")
            if sysfs_path.exists():
                try:
                    interfaces = [
                        entry.name for entry in sysfs_path.iterdir() if entry.is_dir()
                    ]
                except Exception as exc:
                    logger.warning("Error reading /sys/class/net: %s", exc)

        filtered = [iface for iface in interfaces if iface]
        unique_order_preserved = list(dict.fromkeys(filtered))

        prioritized = PacketSniffer._prioritize_interfaces(unique_order_preserved)
        logger.info("Available interfaces (prioritized): %s", prioritized)
        return prioritized

    @staticmethod
    def _match_interface(target: Optional[str], interfaces: List[str]) -> Optional[str]:
        if not target:
            return None
        for iface in interfaces:
            if iface == target:
                return iface
        lower_target = target.lower()
        for iface in interfaces:
            if iface.lower() == lower_target:
                return iface
        return None

    @staticmethod
    def _is_loopback(iface: Optional[str]) -> bool:
        if not iface:
            return False
        iface_lower = iface.lower()
        return (
            iface_lower in PacketSniffer.LOOPBACK_NAMES
            or any(iface_lower.startswith(prefix) for prefix in PacketSniffer.LOOPBACK_PREFIXES)
        )

    @staticmethod
    def _prioritize_interfaces(interfaces: List[str]) -> List[str]:

        def priority(name: str):
            lower = name.lower()
            if PacketSniffer._is_loopback(lower):
                return 5, name
            if lower.startswith(PacketSniffer.WIRED_PREFIXES):
                return 0, name
            if lower.startswith(PacketSniffer.WIRELESS_PREFIXES):
                return 1, name
            if lower.startswith(PacketSniffer.VIRTUAL_PREFIXES):
                return 3, name
            return 2, name

        return sorted(interfaces, key=priority)

    def clear_packets(self):
        """Clear stored packets from memory"""
        count = len(self.packets)
        self.packets.clear()
        logger.info("Cleared %d packets from memory", count)


def sniff_packets(
    interface: Optional[str] = None,
    count: int = 0,
    timeout: Optional[int] = None,
    filter_rule: Optional[str] = None
) -> List[Packet]:
    """
    Convenience function for quick packet capture

    Args:
        interface: Network interface
        count: Number of packets
        timeout: Capture timeout
        filter_rule: BPF filter

    Returns:
        List of captured packets
    """
    sniffer = PacketSniffer(interface)
    return sniffer.sniff_packets(count=count, timeout=timeout, filter_rule=filter_rule)
