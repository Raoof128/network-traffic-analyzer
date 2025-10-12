"""
HTML Report Generator
Generate comprehensive HTML reports for traffic analysis
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import pandas as pd
import base64
from io import BytesIO
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate HTML reports for traffic analysis"""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        plt.close(fig)
        return f"data:image/png;base64,{img_base64}"

    def _create_css(self) -> str:
        """Generate CSS styles for report"""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }

            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }

            h2 {
                color: #34495e;
                margin-top: 30px;
                margin-bottom: 15px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }

            .header-info {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 30px;
            }

            .header-info p {
                margin: 5px 0;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }

            .metric-card {
                background: #ecf0f1;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }

            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #3498db;
            }

            .metric-label {
                color: #7f8c8d;
                margin-top: 5px;
            }

            .alert-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }

            .alert-table th, .alert-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }

            .alert-table th {
                background: #34495e;
                color: white;
            }

            .alert-table tr:hover {
                background: #f5f5f5;
            }

            .severity-high {
                color: #e74c3c;
                font-weight: bold;
            }

            .severity-medium {
                color: #f39c12;
                font-weight: bold;
            }

            .severity-low {
                color: #27ae60;
                font-weight: bold;
            }

            .chart-container {
                margin: 30px 0;
                text-align: center;
            }

            .chart-container img {
                max-width: 100%;
                height: auto;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }

            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #7f8c8d;
            }
        </style>
        """

    def generate_summary_report(
        self,
        analysis_results: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive HTML summary report

        Args:
            analysis_results: Dictionary with analysis results
            output_path: Path to save report

        Returns:
            Path to generated report

        Example:
            >>> generator = HTMLReportGenerator()
            >>> report_path = generator.generate_summary_report(results)
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.output_dir, f"analysis_report_{timestamp}.html")

        # Extract data from results
        metrics = analysis_results.get('metrics', {})
        alerts = analysis_results.get('alerts', [])
        traffic_stats = analysis_results.get('traffic_stats', {})

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Traffic Analysis Report</title>
    {self._create_css()}
</head>
<body>
    <div class="container">
        <h1>🛡️ Network Traffic Analysis Report</h1>

        <div class="header-info">
            <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Analysis Period:</strong> {analysis_results.get('period', 'N/A')}</p>
            <p><strong>Total Packets Analyzed:</strong> {traffic_stats.get('total_packets', 0):,}</p>
        </div>

        <h2>📊 Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics.get('anomaly_count', 0)}</div>
                <div class="metric-label">Anomalies Detected</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('anomaly_rate', 0):.2%}</div>
                <div class="metric-label">Anomaly Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{traffic_stats.get('total_bytes', 0):,}</div>
                <div class="metric-label">Total Bytes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(traffic_stats.get('unique_ips', []))}</div>
                <div class="metric-label">Unique IP Addresses</div>
            </div>
        </div>

        <h2>⚠️ Recent Alerts</h2>
        {self._generate_alert_table(alerts[:20])}

        <h2>📈 Traffic Statistics</h2>
        {self._generate_traffic_stats(traffic_stats)}

        <div class="footer">
            <p>Generated by Network Traffic Analyzer | © {datetime.now().year}</p>
        </div>
    </div>
</body>
</html>
        """

        # Write to file
        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"Generated HTML report: {output_path}")
        return output_path

    def _generate_alert_table(self, alerts: List[Dict[str, Any]]) -> str:
        """Generate HTML table for alerts"""
        if not alerts:
            return "<p>No alerts to display.</p>"

        rows = ""
        for alert in alerts:
            severity_class = f"severity-{alert.get('severity', 'low').lower()}"
            rows += f"""
            <tr>
                <td>{alert.get('timestamp', 'N/A')}</td>
                <td class="{severity_class}">{alert.get('severity', 'N/A')}</td>
                <td>{alert.get('anomaly_type', 'N/A')}</td>
                <td>{alert.get('src_ip', 'N/A')}</td>
                <td>{alert.get('dst_ip', 'N/A')}</td>
                <td>{alert.get('protocol', 'N/A')}</td>
            </tr>
            """

        return f"""
        <table class="alert-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Severity</th>
                    <th>Type</th>
                    <th>Source IP</th>
                    <th>Destination IP</th>
                    <th>Protocol</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_traffic_stats(self, stats: Dict[str, Any]) -> str:
        """Generate traffic statistics section"""
        protocol_dist = stats.get('protocol_distribution', {})

        protocol_rows = ""
        for protocol, count in protocol_dist.items():
            protocol_rows += f"<li><strong>{protocol}:</strong> {count:,} packets</li>"

        return f"""
        <div>
            <h3>Protocol Distribution</h3>
            <ul>
                {protocol_rows}
            </ul>

            <h3>Top Source IPs</h3>
            <ul>
                {self._generate_ip_list(stats.get('top_src_ips', []))}
            </ul>

            <h3>Top Destination IPs</h3>
            <ul>
                {self._generate_ip_list(stats.get('top_dst_ips', []))}
            </ul>
        </div>
        """

    def _generate_ip_list(self, ip_list: List[tuple]) -> str:
        """Generate HTML list for IP addresses"""
        if not ip_list:
            return "<li>No data available</li>"

        items = ""
        for ip, count in ip_list[:10]:
            items += f"<li><strong>{ip}:</strong> {count:,} packets</li>"

        return items


def generate_html_report(analysis_results: Dict[str, Any], output_path: str) -> str:
    """
    Convenience function to generate HTML report

    Args:
        analysis_results: Analysis results dictionary
        output_path: Output file path

    Returns:
        Path to generated report
    """
    generator = HTMLReportGenerator()
    return generator.generate_summary_report(analysis_results, output_path)
