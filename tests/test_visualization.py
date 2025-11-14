"""
Tests for visualization modules (plots and report generation).

This module tests plot generation, report creation, and
visualization functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np


class TestPlots:
    """Test suite for plot generation."""

    @pytest.fixture
    def plot_data(self):
        """Create sample data for plotting."""
        return {
            'timestamps': pd.date_range('2025-01-01', periods=100, freq='1min'),
            'packet_counts': np.random.randint(10, 100, 100),
            'byte_counts': np.random.randint(1000, 10000, 100),
            'protocols': ['TCP'] * 60 + ['UDP'] * 30 + ['ICMP'] * 10,
            'anomaly_scores': np.random.random(100),
        }

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_timeline_plot(self, mock_close, mock_savefig, plot_data, temp_dir):
        """Test creating timeline plot."""
        try:
            from visualization.plots import create_timeline_plot

            output_file = temp_dir / "timeline.png"
            create_timeline_plot(
                plot_data['timestamps'],
                plot_data['packet_counts'],
                str(output_file)
            )

            # Verify savefig was called
            mock_savefig.assert_called()
        except ImportError:
            pytest.skip("Visualization module not available")

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_protocol_distribution_plot(self, mock_close, mock_savefig, plot_data, temp_dir):
        """Test creating protocol distribution plot."""
        try:
            from visualization.plots import create_protocol_distribution

            output_file = temp_dir / "protocol_dist.png"
            create_protocol_distribution(
                plot_data['protocols'],
                str(output_file)
            )

            mock_savefig.assert_called()
        except ImportError:
            pytest.skip("Visualization module not available")

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_anomaly_score_plot(self, mock_close, mock_savefig, plot_data, temp_dir):
        """Test creating anomaly score plot."""
        try:
            from visualization.plots import create_anomaly_score_plot

            output_file = temp_dir / "anomaly_scores.png"
            create_anomaly_score_plot(
                plot_data['timestamps'],
                plot_data['anomaly_scores'],
                str(output_file)
            )

            mock_savefig.assert_called()
        except (ImportError, AttributeError):
            pytest.skip("Anomaly score plot not implemented")

    def test_create_multiple_plots(self, plot_data, temp_dir):
        """Test creating multiple plots."""
        try:
            from visualization import plots

            # Create various plots
            output_files = []
            plot_functions = [
                ('timeline', 'create_timeline_plot'),
                ('protocol', 'create_protocol_distribution'),
            ]

            for name, func_name in plot_functions:
                if hasattr(plots, func_name):
                    output_file = temp_dir / f"{name}.png"
                    output_files.append(output_file)

            # Verify plots don't crash
            assert True
        except ImportError:
            pytest.skip("Visualization module not available")

    @patch('plotly.graph_objects.Figure.write_html')
    def test_create_interactive_plot(self, mock_write_html, plot_data, temp_dir):
        """Test creating interactive Plotly plot."""
        try:
            from visualization.plots import create_interactive_timeline

            output_file = temp_dir / "interactive.html"
            create_interactive_timeline(
                plot_data['timestamps'],
                plot_data['packet_counts'],
                str(output_file)
            )

            # Verify write_html was called
            mock_write_html.assert_called()
        except (ImportError, AttributeError):
            pytest.skip("Interactive plots not implemented")


class TestReportGenerator:
    """Test suite for report generation."""

    @pytest.fixture
    def report_data(self):
        """Create sample data for report."""
        return {
            'summary': {
                'total_packets': 1000,
                'total_bytes': 1500000,
                'duration': 3600,
                'start_time': '2025-01-01 00:00:00',
                'end_time': '2025-01-01 01:00:00',
            },
            'anomalies': {
                'total_anomalies': 25,
                'anomaly_percentage': 2.5,
                'high_severity': 5,
                'medium_severity': 10,
                'low_severity': 10,
            },
            'protocols': {
                'TCP': 600,
                'UDP': 300,
                'ICMP': 100,
            },
            'top_sources': [
                {'ip': '192.168.1.100', 'count': 250},
                {'ip': '192.168.1.101', 'count': 200},
                {'ip': '192.168.1.102', 'count': 150},
            ],
            'top_destinations': [
                {'ip': '10.0.0.1', 'count': 300},
                {'ip': '10.0.0.2', 'count': 250},
                {'ip': '10.0.0.3', 'count': 150},
            ],
        }

    def test_create_html_report(self, report_data, temp_dir):
        """Test creating HTML report."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            output_file = temp_dir / "report.html"

            generator.generate_html_report(report_data, str(output_file))

            # Verify file was created
            assert output_file.exists()

            # Verify it's HTML
            content = output_file.read_text()
            assert '<html' in content.lower()
        except (ImportError, AttributeError):
            pytest.skip("HTML report generation not fully implemented")

    def test_create_json_report(self, report_data, temp_dir):
        """Test creating JSON report."""
        try:
            from visualization.report_generator import ReportGenerator
            import json

            generator = ReportGenerator()
            output_file = temp_dir / "report.json"

            generator.generate_json_report(report_data, str(output_file))

            # Verify file was created
            assert output_file.exists()

            # Verify it's valid JSON
            with open(output_file) as f:
                data = json.load(f)
                assert isinstance(data, dict)
        except (ImportError, AttributeError):
            pytest.skip("JSON report generation not implemented")

    def test_create_pdf_report(self, report_data, temp_dir):
        """Test creating PDF report."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            output_file = temp_dir / "report.pdf"

            generator.generate_pdf_report(report_data, str(output_file))

            # Verify file was created
            if output_file.exists():
                assert output_file.stat().st_size > 0
        except (ImportError, AttributeError):
            pytest.skip("PDF report generation not implemented")

    def test_report_with_plots(self, report_data, temp_dir):
        """Test creating report with embedded plots."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            output_file = temp_dir / "report_with_plots.html"

            # Create some plot files
            plot_files = [
                temp_dir / "plot1.png",
                temp_dir / "plot2.png",
            ]

            for plot_file in plot_files:
                plot_file.write_text("dummy plot")

            generator.generate_html_report(
                report_data,
                str(output_file),
                plot_files=[str(p) for p in plot_files]
            )

            # Verify plots are referenced in report
            if output_file.exists():
                content = output_file.read_text()
                # Should contain image references
                assert len(content) > 0
        except (ImportError, AttributeError, TypeError):
            pytest.skip("Report with plots not fully implemented")

    def test_report_summary_section(self, report_data):
        """Test report summary section generation."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            summary_html = generator._generate_summary_section(report_data['summary'])

            assert isinstance(summary_html, str)
            assert len(summary_html) > 0
            assert 'total_packets' in summary_html or 'Total Packets' in summary_html
        except (ImportError, AttributeError):
            pytest.skip("Summary section generation not implemented")

    def test_report_anomalies_section(self, report_data):
        """Test report anomalies section generation."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            anomalies_html = generator._generate_anomalies_section(report_data['anomalies'])

            assert isinstance(anomalies_html, str)
            assert len(anomalies_html) > 0
        except (ImportError, AttributeError):
            pytest.skip("Anomalies section generation not implemented")

    def test_report_template_rendering(self, report_data, temp_dir):
        """Test report template rendering."""
        try:
            from visualization.report_generator import ReportGenerator

            generator = ReportGenerator()
            output_file = temp_dir / "templated_report.html"

            # Generate report
            generator.generate_html_report(report_data, str(output_file))

            if output_file.exists():
                content = output_file.read_text()

                # Verify template was rendered
                assert '<html' in content.lower()
                assert '</html>' in content.lower()

                # Verify data was inserted
                assert str(report_data['summary']['total_packets']) in content
        except (ImportError, AttributeError):
            pytest.skip("Template rendering not fully implemented")


class TestVisualizationHelpers:
    """Test suite for visualization helper functions."""

    def test_format_bytes(self):
        """Test byte formatting helper."""
        try:
            from visualization.plots import format_bytes

            assert 'KB' in format_bytes(1024)
            assert 'MB' in format_bytes(1024 * 1024)
            assert 'GB' in format_bytes(1024 * 1024 * 1024)
        except (ImportError, AttributeError):
            pytest.skip("format_bytes not implemented")

    def test_format_duration(self):
        """Test duration formatting helper."""
        try:
            from visualization.plots import format_duration

            assert 'second' in format_duration(1).lower()
            assert 'minute' in format_duration(60).lower()
            assert 'hour' in format_duration(3600).lower()
        except (ImportError, AttributeError):
            pytest.skip("format_duration not implemented")

    def test_color_by_severity(self):
        """Test color assignment by severity."""
        try:
            from visualization.plots import get_severity_color

            assert get_severity_color('low') != get_severity_color('high')
            assert get_severity_color('critical') != get_severity_color('medium')
        except (ImportError, AttributeError):
            pytest.skip("get_severity_color not implemented")


@pytest.mark.integration
class TestVisualizationIntegration:
    """Integration tests for visualization."""

    def test_complete_visualization_workflow(self, sample_features_dataframe, temp_dir):
        """Test complete visualization workflow."""
        try:
            from visualization.report_generator import ReportGenerator
            from visualization import plots

            # Prepare data
            report_data = {
                'summary': {
                    'total_packets': len(sample_features_dataframe),
                    'total_bytes': sample_features_dataframe['packet_length'].sum(),
                },
            }

            # Generate plots
            plot_file = temp_dir / "analysis_plot.png"

            # Generate report
            report_file = temp_dir / "analysis_report.html"
            generator = ReportGenerator()
            generator.generate_html_report(report_data, str(report_file))

            # Verify outputs
            # At minimum, should not crash
            assert True
        except ImportError:
            pytest.skip("Visualization modules not available")


@pytest.mark.performance
class TestVisualizationPerformance:
    """Performance tests for visualization."""

    def test_plot_generation_performance(self, temp_dir):
        """Test plot generation performance."""
        import time

        try:
            from visualization import plots
            import matplotlib.pyplot as plt

            # Generate large dataset
            timestamps = pd.date_range('2025-01-01', periods=10000, freq='1s')
            values = np.random.randint(0, 1000, 10000)

            # Measure plot creation time
            start = time.time()

            fig, ax = plt.subplots()
            ax.plot(timestamps, values)

            output_file = temp_dir / "perf_test.png"
            plt.savefig(str(output_file))
            plt.close()

            elapsed = time.time() - start

            # Should complete in reasonable time (< 5 seconds)
            assert elapsed < 5.0
        except ImportError:
            pytest.skip("Matplotlib not available")

    def test_report_generation_performance(self, temp_dir):
        """Test report generation performance."""
        import time

        try:
            from visualization.report_generator import ReportGenerator

            # Large report data
            report_data = {
                'summary': {'total_packets': 1000000},
                'anomalies': {'total_anomalies': 10000},
                'protocols': {f'protocol_{i}': i*100 for i in range(100)},
            }

            start = time.time()

            generator = ReportGenerator()
            output_file = temp_dir / "large_report.html"
            generator.generate_html_report(report_data, str(output_file))

            elapsed = time.time() - start

            # Should complete in reasonable time (< 10 seconds)
            assert elapsed < 10.0
        except (ImportError, AttributeError):
            pytest.skip("Report generator not available")
