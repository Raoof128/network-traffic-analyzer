"""
Unit tests for capture module
"""

from types import SimpleNamespace

import pytest
from scapy.all import Ether, IP, TCP, UDP

import capture.packet_sniffer as packet_sniffer_module
from capture.packet_sniffer import PacketSniffer
from capture.pcap_handler import PcapHandler


class TestPcapHandler:
    """Test PCAP file operations"""

    def test_write_and_read_pcap(self, tmp_path):
        """Test writing and reading PCAP files"""
        packets = [
            Ether() / IP(src="192.168.1.1", dst="192.168.1.2") / TCP(sport=80, dport=443),
            Ether() / IP(src="192.168.1.2", dst="192.168.1.1") / UDP(sport=53, dport=5353),
        ]

        pcap_file = tmp_path / "test.pcap"
        PcapHandler.write_pcap(packets, str(pcap_file))
        assert pcap_file.exists()

        loaded_packets = PcapHandler.read_pcap(str(pcap_file))
        assert len(loaded_packets) == len(packets)
        assert loaded_packets[0].haslayer(TCP)
        assert loaded_packets[1].haslayer(UDP)

    def test_pcap_info(self, tmp_path):
        """Test getting PCAP file info"""
        packets = [Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP()]
        pcap_file = tmp_path / "info_test.pcap"
        PcapHandler.write_pcap(packets, str(pcap_file))

        info = PcapHandler.get_pcap_info(str(pcap_file))

        assert info["packet_count"] == 1
        assert info["file_size"] > 0
        assert "filename" in info

    def test_filter_and_save(self, tmp_path):
        """Test filtering packets and saving"""
        packets = [
            Ether() / IP() / TCP(dport=80),
            Ether() / IP() / TCP(dport=443),
            Ether() / IP() / UDP(dport=53),
        ]

        input_file = tmp_path / "input.pcap"
        output_file = tmp_path / "output.pcap"

        PcapHandler.write_pcap(packets, str(input_file))

        PcapHandler.filter_and_save(
            str(input_file),
            str(output_file),
            lambda pkt: pkt.haslayer(TCP),
        )

        filtered = PcapHandler.read_pcap(str(output_file))
        assert len(filtered) == 2
        assert all(pkt.haslayer(TCP) for pkt in filtered)


class TestPacketSniffer:
    """Test packet sniffing functionality"""

    def test_sniffer_initialization(self):
        """Test sniffer initialization"""
        sniffer = PacketSniffer()
        assert sniffer.interface is not None
        assert isinstance(sniffer.packets, list)

    def test_clear_packets(self):
        """Test clearing packet buffer"""
        sniffer = PacketSniffer()
        sniffer.packets = [1, 2, 3]
        sniffer.clear_packets()
        assert len(sniffer.packets) == 0

    def test_get_available_interfaces(self):
        """Test getting available network interfaces"""
        interfaces = PacketSniffer.get_available_interfaces()
        assert isinstance(interfaces, list)
        assert len(interfaces) > 0

    def test_resolve_interface_requested_available(self, monkeypatch):
        """Requested interface is respected when available"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: ["eth0", "lo"]),
            raising=False,
        )
        assert PacketSniffer.resolve_interface("eth0") == "eth0"

    def test_resolve_interface_case_insensitive(self, monkeypatch):
        """Resolve interface should be case-insensitive"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: ["Enp0s3"]),
            raising=False,
        )
        assert PacketSniffer.resolve_interface("enp0s3") == "Enp0s3"

    def test_resolve_interface_prefers_default_when_valid(self, monkeypatch):
        """Prefer Scapy default interface when it is available and non-loopback"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: ["eth0", "lo"]),
            raising=False,
        )
        monkeypatch.setattr(
            packet_sniffer_module,
            "conf",
            SimpleNamespace(iface="eth0"),
            raising=False,
        )
        assert PacketSniffer.resolve_interface(None) == "eth0"

    def test_resolve_interface_skips_loopback_default(self, monkeypatch):
        """Skip loopback default when other interfaces exist"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: ["lo", "eth0"]),
            raising=False,
        )
        monkeypatch.setattr(
            packet_sniffer_module,
            "conf",
            SimpleNamespace(iface="lo"),
            raising=False,
        )
        assert PacketSniffer.resolve_interface(None) == "eth0"

    def test_resolve_interface_only_loopback(self, monkeypatch):
        """Use loopback when it is the only option"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: ["lo"]),
            raising=False,
        )
        monkeypatch.setattr(
            packet_sniffer_module,
            "conf",
            SimpleNamespace(iface="lo"),
            raising=False,
        )
        assert PacketSniffer.resolve_interface(None) == "lo"

    def test_resolve_interface_no_interfaces(self, monkeypatch):
        """Raise error when no interfaces are detected"""
        monkeypatch.setattr(
            PacketSniffer,
            "get_available_interfaces",
            staticmethod(lambda: []),
            raising=False,
        )
        with pytest.raises(ValueError):
            PacketSniffer.resolve_interface(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
