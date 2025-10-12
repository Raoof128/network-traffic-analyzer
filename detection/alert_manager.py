"""
Alert Management System
Handle anomaly alerts with multiple notification channels
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Manage anomaly alerts and notifications"""

    def __init__(
        self,
        log_file: str = "logs/alerts.log",
        console_output: bool = True,
        save_to_file: bool = True
    ):
        """
        Initialize alert manager

        Args:
            log_file: Path to alert log file
            console_output: Enable console output
            save_to_file: Save alerts to file

        Example:
            >>> alert_mgr = AlertManager(log_file="logs/alerts.log")
            >>> alert_mgr.generate_alert("anomaly", packet_info, AlertSeverity.HIGH)
        """
        self.log_file = log_file
        self.console_output = console_output
        self.save_to_file = save_to_file

        self.alert_history: List[Dict[str, Any]] = []
        self.alert_count = 0

        # Create log directory
        if self.save_to_file:
            os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs', exist_ok=True)

        logger.info(f"Initialized AlertManager (log_file={log_file})")

    def generate_alert(
        self,
        anomaly_type: str,
        packet_info: Dict[str, Any],
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        additional_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate an anomaly alert

        Args:
            anomaly_type: Type of anomaly detected
            packet_info: Information about the anomalous packet/flow
            severity: Alert severity level
            additional_info: Additional context

        Returns:
            Alert dictionary

        Example:
            >>> alert = alert_mgr.generate_alert(
            ...     "port_scan",
            ...     {"src_ip": "192.168.1.100", "dst_ip": "10.0.0.1"},
            ...     AlertSeverity.HIGH
            ... )
        """
        alert = {
            'alert_id': self.alert_count,
            'timestamp': datetime.now().isoformat(),
            'anomaly_type': anomaly_type,
            'severity': severity.value,
            'src_ip': packet_info.get('src_ip'),
            'dst_ip': packet_info.get('dst_ip'),
            'src_port': packet_info.get('src_port'),
            'dst_port': packet_info.get('dst_port'),
            'protocol': packet_info.get('protocol'),
            'packet_size': packet_info.get('packet_size'),
            'additional_info': additional_info or {}
        }

        self.alert_count += 1
        self.alert_history.append(alert)

        # Output to console
        if self.console_output:
            self._print_alert(alert)

        # Save to file
        if self.save_to_file:
            self._save_alert(alert)

        return alert

    def _print_alert(self, alert: Dict[str, Any]):
        """Print alert to console"""
        severity_icons = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'CRITICAL': '🔴'
        }

        icon = severity_icons.get(alert['severity'], '⚠️')

        print(f"\n{icon} ALERT [{alert['severity']}] - {alert['anomaly_type']}")
        print(f"   Timestamp: {alert['timestamp']}")
        print(f"   Source: {alert['src_ip']}:{alert['src_port']}")
        print(f"   Destination: {alert['dst_ip']}:{alert['dst_port']}")
        print(f"   Protocol: {alert['protocol']}")

        if alert.get('additional_info'):
            print(f"   Info: {alert['additional_info']}")

        print("-" * 60)

    def _save_alert(self, alert: Dict[str, Any]):
        """Save alert to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            logger.error(f"Error saving alert to file: {e}")

    def send_notification(
        self,
        alert: Dict[str, Any],
        channels: List[str] = ['console']
    ):
        """
        Send alert notifications through specified channels

        Args:
            alert: Alert dictionary
            channels: List of notification channels ('console', 'file', 'email', 'webhook')

        Example:
            >>> alert_mgr.send_notification(alert, channels=['console', 'file'])
        """
        for channel in channels:
            if channel == 'console':
                self._print_alert(alert)
            elif channel == 'file':
                self._save_alert(alert)
            elif channel == 'email':
                self._send_email_alert(alert)
            elif channel == 'webhook':
                self._send_webhook_alert(alert)
            else:
                logger.warning(f"Unknown notification channel: {channel}")

    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert (placeholder - requires SMTP configuration)"""
        logger.info(f"Email alert would be sent: {alert['anomaly_type']}")
        # TODO: Implement SMTP email sending
        # import smtplib
        # from email.mime.text import MIMEText
        pass

    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook alert (placeholder - requires webhook URL)"""
        logger.info(f"Webhook alert would be sent: {alert['anomaly_type']}")
        # TODO: Implement webhook POST request
        # import requests
        # requests.post(webhook_url, json=alert)
        pass

    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get summary of alerts

        Returns:
            Summary statistics
        """
        if not self.alert_history:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_type': {}
            }

        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            atype = alert['anomaly_type']
            type_counts[atype] = type_counts.get(atype, 0) + 1

        return {
            'total_alerts': len(self.alert_history),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'recent_alerts': self.alert_history[-10:]  # Last 10 alerts
        }

    def print_summary(self):
        """Print alert summary to console"""
        summary = self.get_alert_summary()

        print("\n" + "="*60)
        print("ALERT SUMMARY")
        print("="*60)
        print(f"Total Alerts: {summary['total_alerts']}")
        print("\nBy Severity:")
        for severity, count in summary['by_severity'].items():
            print(f"  {severity}: {count}")

        print("\nBy Type:")
        for atype, count in summary['by_type'].items():
            print(f"  {atype}: {count}")

        print("="*60 + "\n")

    def clear_alerts(self):
        """Clear alert history"""
        count = len(self.alert_history)
        self.alert_history.clear()
        self.alert_count = 0
        logger.info(f"Cleared {count} alerts from history")

    def export_alerts(self, output_file: str, format: str = 'json'):
        """
        Export alerts to file

        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
        """
        try:
            if format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(self.alert_history, f, indent=2)

            elif format == 'csv':
                import pandas as pd
                df = pd.DataFrame(self.alert_history)
                df.to_csv(output_file, index=False)

            logger.info(f"Exported {len(self.alert_history)} alerts to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting alerts: {e}")


class RuleBasedAlertManager(AlertManager):
    """Alert manager with rule-based filtering"""

    def __init__(
        self,
        log_file: str = "logs/alerts.log",
        min_severity: AlertSeverity = AlertSeverity.LOW,
        alert_rate_limit: int = 100
    ):
        """
        Initialize rule-based alert manager

        Args:
            log_file: Alert log file
            min_severity: Minimum severity to trigger alerts
            alert_rate_limit: Maximum alerts per minute
        """
        super().__init__(log_file=log_file)
        self.min_severity = min_severity
        self.alert_rate_limit = alert_rate_limit
        self.recent_alerts = []

    def should_alert(self, severity: AlertSeverity) -> bool:
        """Check if alert should be triggered based on rules"""
        # Check severity threshold
        severity_order = {
            AlertSeverity.LOW: 0,
            AlertSeverity.MEDIUM: 1,
            AlertSeverity.HIGH: 2,
            AlertSeverity.CRITICAL: 3
        }

        if severity_order[severity] < severity_order[self.min_severity]:
            return False

        # Check rate limit (simplified - count in last minute)
        current_time = datetime.now()
        self.recent_alerts = [
            t for t in self.recent_alerts
            if (current_time - t).total_seconds() < 60
        ]

        if len(self.recent_alerts) >= self.alert_rate_limit:
            logger.warning(f"Alert rate limit reached ({self.alert_rate_limit}/min)")
            return False

        self.recent_alerts.append(current_time)
        return True

    def generate_alert(
        self,
        anomaly_type: str,
        packet_info: Dict[str, Any],
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        additional_info: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate alert if rules are satisfied"""
        if self.should_alert(severity):
            return super().generate_alert(anomaly_type, packet_info, severity, additional_info)
        return None


# Convenience function
def create_alert(
    anomaly_type: str,
    packet_info: Dict[str, Any],
    severity: str = "MEDIUM"
) -> Dict[str, Any]:
    """
    Convenience function to create an alert

    Args:
        anomaly_type: Type of anomaly
        packet_info: Packet information
        severity: Severity level string

    Returns:
        Alert dictionary
    """
    mgr = AlertManager()
    severity_enum = AlertSeverity[severity.upper()]
    return mgr.generate_alert(anomaly_type, packet_info, severity_enum)
