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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

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
        save_to_file: bool = True,
        email_config: Optional[Dict[str, Any]] = None,
        webhook_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize alert manager

        Args:
            log_file: Path to alert log file
            console_output: Enable console output
            save_to_file: Save alerts to file
            email_config: Email configuration (smtp_server, smtp_port, use_tls, sender, password, recipients)
            webhook_config: Webhook configuration (url, method, headers, timeout)

        Example:
            >>> email_cfg = {
            ...     'smtp_server': 'smtp.gmail.com',
            ...     'smtp_port': 587,
            ...     'use_tls': True,
            ...     'sender': 'alerts@example.com',
            ...     'password': 'your_password',
            ...     'recipients': ['admin@example.com']
            ... }
            >>> alert_mgr = AlertManager(log_file="logs/alerts.log", email_config=email_cfg)
            >>> alert_mgr.generate_alert("anomaly", packet_info, AlertSeverity.HIGH)
        """
        self.log_file = log_file
        self.console_output = console_output
        self.save_to_file = save_to_file
        self.email_config = email_config or {}
        self.webhook_config = webhook_config or {}

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
        """
        Send email alert via SMTP

        Args:
            alert: Alert dictionary to send
        """
        if not self.email_config:
            logger.warning("Email configuration not provided. Skipping email alert.")
            return

        try:
            # Extract email configuration
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port', 587)
            use_tls = self.email_config.get('use_tls', True)
            sender = self.email_config.get('sender')
            password = self.email_config.get('password')
            recipients = self.email_config.get('recipients', [])
            subject_prefix = self.email_config.get('subject_prefix', '[Network Traffic Analyzer]')

            if not all([smtp_server, sender, password, recipients]):
                logger.warning("Incomplete email configuration. Required: smtp_server, sender, password, recipients")
                return

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"{subject_prefix} {alert['severity']} Alert - {alert['anomaly_type']}"

            # Create HTML email body
            html_body = f"""
            <html>
              <head></head>
              <body>
                <h2 style="color: {'#ff0000' if alert['severity'] == 'CRITICAL' else '#ff6600' if alert['severity'] == 'HIGH' else '#ffcc00' if alert['severity'] == 'MEDIUM' else '#00cc00'};">
                  {alert['severity']} Alert: {alert['anomaly_type']}
                </h2>
                <table style="border-collapse: collapse; width: 100%;">
                  <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Alert ID</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['alert_id']}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Timestamp</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['timestamp']}</td>
                  </tr>
                  <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Source IP:Port</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['src_ip']}:{alert['src_port']}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Destination IP:Port</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['dst_ip']}:{alert['dst_port']}</td>
                  </tr>
                  <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Protocol</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['protocol']}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Packet Size</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert['packet_size']} bytes</td>
                  </tr>
            """

            if alert.get('additional_info'):
                html_body += f"""
                  <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Additional Info</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{json.dumps(alert['additional_info'], indent=2)}</td>
                  </tr>
                """

            html_body += """
                </table>
                <br>
                <p style="color: #666; font-size: 12px;">
                  This is an automated alert from Network Traffic Analyzer. Please review and take appropriate action.
                </p>
              </body>
            </html>
            """

            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))

            # Send email via SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(sender, password)
                server.send_message(msg)

            logger.info(f"Email alert sent successfully to {len(recipients)} recipient(s): {alert['anomaly_type']}")

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email alert: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending email alert: {e}")

    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """
        Send webhook alert via HTTP POST

        Args:
            alert: Alert dictionary to send
        """
        if not self.webhook_config:
            logger.warning("Webhook configuration not provided. Skipping webhook alert.")
            return

        try:
            # Extract webhook configuration
            url = self.webhook_config.get('url')
            method = self.webhook_config.get('method', 'POST').upper()
            headers = self.webhook_config.get('headers', {'Content-Type': 'application/json'})
            timeout = self.webhook_config.get('timeout', 10)
            retry_attempts = self.webhook_config.get('retry_attempts', 3)
            retry_delay = self.webhook_config.get('retry_delay', 1)

            if not url:
                logger.warning("Webhook URL not provided. Skipping webhook alert.")
                return

            # Prepare payload
            payload = {
                'alert_id': alert['alert_id'],
                'timestamp': alert['timestamp'],
                'severity': alert['severity'],
                'anomaly_type': alert['anomaly_type'],
                'source': {
                    'ip': alert['src_ip'],
                    'port': alert['src_port']
                },
                'destination': {
                    'ip': alert['dst_ip'],
                    'port': alert['dst_port']
                },
                'protocol': alert['protocol'],
                'packet_size': alert['packet_size'],
                'additional_info': alert.get('additional_info', {})
            }

            # Send webhook with retry logic
            for attempt in range(retry_attempts):
                try:
                    if method == 'POST':
                        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                    elif method == 'PUT':
                        response = requests.put(url, json=payload, headers=headers, timeout=timeout)
                    else:
                        logger.error(f"Unsupported HTTP method: {method}")
                        return

                    # Check response status
                    response.raise_for_status()
                    logger.info(f"Webhook alert sent successfully to {url} (status: {response.status_code}): {alert['anomaly_type']}")
                    return

                except requests.exceptions.Timeout:
                    logger.warning(f"Webhook request timeout (attempt {attempt + 1}/{retry_attempts})")
                    if attempt < retry_attempts - 1:
                        import time
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Webhook alert failed after {retry_attempts} attempts: timeout")

                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"Webhook connection error (attempt {attempt + 1}/{retry_attempts}): {e}")
                    if attempt < retry_attempts - 1:
                        import time
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Webhook alert failed after {retry_attempts} attempts: connection error")

                except requests.exceptions.HTTPError as e:
                    logger.error(f"Webhook HTTP error (status {response.status_code}): {e}")
                    # Don't retry on HTTP errors (4xx, 5xx)
                    return

        except Exception as e:
            logger.error(f"Unexpected error sending webhook alert: {e}")

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
