"""
Visualization Module
Generate plots and charts for traffic analysis
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class TrafficVisualizer:
    """Generate traffic analysis visualizations"""

    def __init__(self, output_dir: str = "visualization/plots"):
        """
        Initialize traffic visualizer

        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_traffic_timeline(
        self,
        timestamps: List[float],
        packet_counts: List[int],
        title: str = "Network Traffic Timeline",
        save_path: Optional[str] = None
    ):
        """
        Plot traffic volume over time

        Args:
            timestamps: List of timestamps
            packet_counts: Packet counts per time window
            title: Plot title
            save_path: Path to save plot

        Example:
            >>> viz = TrafficVisualizer()
            >>> viz.plot_traffic_timeline(timestamps, counts)
        """
        plt.figure(figsize=(14, 6))

        # Convert timestamps to datetime
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]

        plt.plot(dates, packet_counts, linewidth=2, color='steelblue')
        plt.fill_between(dates, packet_counts, alpha=0.3, color='steelblue')

        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Packet Count', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved traffic timeline to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'traffic_timeline.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_protocol_distribution(
        self,
        protocol_counts: Dict[str, int],
        title: str = "Protocol Distribution",
        save_path: Optional[str] = None
    ):
        """
        Plot protocol distribution as pie chart

        Args:
            protocol_counts: Dictionary of protocol counts
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(10, 8))

        protocols = list(protocol_counts.keys())
        counts = list(protocol_counts.values())

        colors = sns.color_palette('Set3', len(protocols))
        explode = [0.05] * len(protocols)

        plt.pie(
            counts,
            labels=protocols,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            explode=explode
        )

        plt.title(title, fontsize=16, fontweight='bold')
        plt.axis('equal')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved protocol distribution to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'protocol_distribution.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_anomaly_timeline(
        self,
        anomaly_data: pd.DataFrame,
        title: str = "Anomaly Detection Timeline",
        save_path: Optional[str] = None
    ):
        """
        Plot anomaly timeline with severity levels

        Args:
            anomaly_data: DataFrame with columns ['timestamp', 'severity', 'anomaly_score']
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(14, 6))

        # Define colors for severity levels
        severity_colors = {
            'LOW': 'green',
            'MEDIUM': 'yellow',
            'HIGH': 'orange',
            'CRITICAL': 'red'
        }

        if 'timestamp' in anomaly_data.columns:
            timestamps = pd.to_datetime(anomaly_data['timestamp'])
        else:
            timestamps = range(len(anomaly_data))

        # Plot anomalies with colors based on severity
        for severity, color in severity_colors.items():
            mask = anomaly_data.get('severity', 'MEDIUM') == severity
            if mask.any():
                plt.scatter(
                    timestamps[mask],
                    anomaly_data.loc[mask, 'anomaly_score'] if 'anomaly_score' in anomaly_data.columns else range(sum(mask)),
                    c=color,
                    label=severity,
                    alpha=0.6,
                    s=100
                )

        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Anomaly Score', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved anomaly timeline to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'anomaly_timeline.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_top_ips(
        self,
        ip_counts: Dict[str, int],
        top_n: int = 10,
        title: str = "Top Source IPs",
        save_path: Optional[str] = None
    ):
        """
        Plot top N IP addresses by packet count

        Args:
            ip_counts: Dictionary of IP addresses and counts
            top_n: Number of top IPs to display
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(12, 6))

        # Sort and get top N
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        ips = [ip for ip, _ in sorted_ips]
        counts = [count for _, count in sorted_ips]

        plt.barh(ips, counts, color='steelblue')
        plt.xlabel('Packet Count', fontsize=12)
        plt.ylabel('IP Address', fontsize=12)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved top IPs plot to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'top_ips.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_packet_size_distribution(
        self,
        packet_sizes: List[int],
        title: str = "Packet Size Distribution",
        save_path: Optional[str] = None
    ):
        """
        Plot packet size distribution histogram

        Args:
            packet_sizes: List of packet sizes
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(12, 6))

        plt.hist(packet_sizes, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        plt.axvline(np.mean(packet_sizes), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(packet_sizes):.0f}')
        plt.axvline(np.median(packet_sizes), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(packet_sizes):.0f}')

        plt.xlabel('Packet Size (bytes)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved packet size distribution to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'packet_size_dist.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_feature_importance(
        self,
        feature_names: List[str],
        importances: List[float],
        top_n: int = 15,
        title: str = "Feature Importance",
        save_path: Optional[str] = None
    ):
        """
        Plot feature importance for ML models

        Args:
            feature_names: List of feature names
            importances: List of importance scores
            top_n: Number of top features to display
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(12, 8))

        # Sort by importance
        indices = np.argsort(importances)[-top_n:]
        top_features = [feature_names[i] for i in indices]
        top_importances = [importances[i] for i in indices]

        plt.barh(top_features, top_importances, color='steelblue')
        plt.xlabel('Importance Score', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved feature importance to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'feature_importance.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def plot_port_activity(
        self,
        port_counts: Dict[int, int],
        top_n: int = 20,
        title: str = "Port Activity",
        save_path: Optional[str] = None
    ):
        """
        Plot port activity

        Args:
            port_counts: Dictionary of ports and packet counts
            top_n: Number of top ports to display
            title: Plot title
            save_path: Path to save plot
        """
        plt.figure(figsize=(14, 6))

        # Sort and get top N
        sorted_ports = sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        ports = [str(port) for port, _ in sorted_ports]
        counts = [count for _, count in sorted_ports]

        plt.bar(ports, counts, color='steelblue')
        plt.xlabel('Port', fontsize=12)
        plt.ylabel('Packet Count', fontsize=12)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved port activity to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'port_activity.png'), dpi=300, bbox_inches='tight')

        plt.close()

    def create_dashboard(
        self,
        traffic_data: pd.DataFrame,
        anomaly_data: Optional[pd.DataFrame] = None,
        save_path: Optional[str] = None
    ):
        """
        Create comprehensive dashboard with multiple plots

        Args:
            traffic_data: DataFrame with traffic features
            anomaly_data: DataFrame with anomaly information
            save_path: Path to save dashboard
        """
        fig, axes = plt.subplots(2, 2, figsize=(20, 12))

        # Plot 1: Traffic timeline
        if 'timestamp' in traffic_data.columns:
            timestamps = traffic_data['timestamp'].values
            axes[0, 0].plot(timestamps, range(len(timestamps)), color='steelblue')
            axes[0, 0].set_title('Traffic Timeline', fontweight='bold')
            axes[0, 0].set_xlabel('Timestamp')
            axes[0, 0].set_ylabel('Packet Count')
            axes[0, 0].grid(True, alpha=0.3)

        # Plot 2: Protocol distribution
        if 'protocol' in traffic_data.columns:
            protocol_counts = traffic_data['protocol'].value_counts()
            axes[0, 1].pie(protocol_counts.values, labels=protocol_counts.index, autopct='%1.1f%%')
            axes[0, 1].set_title('Protocol Distribution', fontweight='bold')

        # Plot 3: Packet size distribution
        if 'packet_size' in traffic_data.columns:
            axes[1, 0].hist(traffic_data['packet_size'].dropna(), bins=30, color='steelblue', alpha=0.7)
            axes[1, 0].set_title('Packet Size Distribution', fontweight='bold')
            axes[1, 0].set_xlabel('Packet Size (bytes)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True, alpha=0.3)

        # Plot 4: Top IPs
        if 'src_ip' in traffic_data.columns:
            ip_counts = traffic_data['src_ip'].value_counts().head(10)
            axes[1, 1].barh(ip_counts.index, ip_counts.values, color='steelblue')
            axes[1, 1].set_title('Top Source IPs', fontweight='bold')
            axes[1, 1].set_xlabel('Packet Count')
            axes[1, 1].grid(True, alpha=0.3)

        plt.suptitle('Network Traffic Analysis Dashboard', fontsize=20, fontweight='bold', y=0.995)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved dashboard to {save_path}")
        else:
            plt.savefig(os.path.join(self.output_dir, 'dashboard.png'), dpi=300, bbox_inches='tight')

        plt.close()


# Convenience functions
def plot_traffic_timeline(timestamps: List[float], packet_counts: List[int], save_path: str = None):
    """Convenience function to plot traffic timeline"""
    viz = TrafficVisualizer()
    viz.plot_traffic_timeline(timestamps, packet_counts, save_path=save_path)


def plot_anomaly_distribution(anomalies: pd.DataFrame, features: List[str], save_path: str = None):
    """Convenience function to plot anomaly distribution"""
    viz = TrafficVisualizer()
    viz.plot_anomaly_timeline(anomalies, save_path=save_path)
