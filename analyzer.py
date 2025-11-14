#!/usr/bin/env python3
"""
Network Traffic Analyzer - Main Entry Point
Real-time and offline network anomaly detection
"""

import argparse
import sys
import logging
import pickle
from pathlib import Path

from capture.packet_sniffer import PacketSniffer
from capture.pcap_handler import PcapHandler
from features.extractor import FeatureExtractor, FlowAggregator
from features.preprocessor import FeaturePreprocessor
from detection.realtime_detector import RealtimeDetector
from detection.alert_manager import AlertManager, AlertSeverity
from visualization.plots import TrafficVisualizer
from visualization.report_generator import HTMLReportGenerator
from models.unsupervised import IsolationForestDetector
from utils.validators import InputValidator, ValidationError
from utils.secure_pickle import safe_load

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Network Traffic Analyzer with ML Anomaly Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Real-time analysis
  sudo python analyzer.py --mode realtime --interface eth0 --model models/trained_models/isolation_forest.pkl

  # Offline PCAP analysis
  python analyzer.py --mode offline --pcap captures/traffic.pcap --output report.html

  # Train new model
  python analyzer.py --mode train --data datasets/training_data.csv --output models/my_model.pkl
        """
    )

    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['realtime', 'offline', 'train'],
        help='Analysis mode: realtime (live capture), offline (pcap file), or train (train model)'
    )

    # Capture options
    parser.add_argument(
        '--interface',
        type=str,
        help='Network interface for real-time capture (e.g., eth0, wlan0)'
    )
    parser.add_argument(
        '--list-interfaces',
        action='store_true',
        help='List available network interfaces and exit'
    )

    parser.add_argument(
        '--pcap',
        type=str,
        help='Path to PCAP file for offline analysis'
    )

    parser.add_argument(
        '--filter',
        type=str,
        help='BPF filter for packet capture (e.g., "tcp port 80")'
    )

    parser.add_argument(
        '--duration',
        type=int,
        help='Capture duration in seconds (for realtime mode)'
    )

    # Model options
    parser.add_argument(
        '--model',
        type=str,
        help='Path to trained model file (.pkl)'
    )

    parser.add_argument(
        '--preprocessor',
        type=str,
        help='Path to preprocessor file (.pkl)'
    )

    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (HTML report for offline, model file for train mode)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/alerts.log',
        help='Alert log file path'
    )

    # Training options
    parser.add_argument(
        '--data',
        type=str,
        help='Training data CSV file path'
    )

    parser.add_argument(
        '--model-type',
        type=str,
        default='isolation_forest',
        choices=['isolation_forest', 'one_class_svm', 'kmeans'],
        help='Model type for training'
    )

    return parser.parse_args()


def realtime_mode(args):
    """Run real-time traffic analysis"""
    logger.info("Starting real-time traffic analysis...")

    try:
        resolved_interface = PacketSniffer.resolve_interface(args.interface)
        if args.interface and args.interface != resolved_interface:
            logger.warning(
                "Requested interface '%s' not available. Using '%s' instead.",
                args.interface,
                resolved_interface
            )
        elif not args.interface:
            logger.info("No interface specified. Using '%s'.", resolved_interface)
        args.interface = resolved_interface
    except ValueError as err:
        logger.error(str(err))
        logger.info("Run the analyzer with --list-interfaces to view valid options.")
        sys.exit(1)

    # Load model
    if not args.model:
        logger.warning("No model specified. Using default Isolation Forest with online training.")
        model = IsolationForestDetector(contamination=0.1)
        # We'll train on first batch
        model_loaded = False
    else:
        try:
            model = safe_load(args.model, restricted=True)
            logger.info(f"Securely loaded model from {args.model}")
            model_loaded = True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            sys.exit(1)

    # Load preprocessor if provided
    preprocessor = None
    if args.preprocessor:
        try:
            preprocessor = FeaturePreprocessor.load(args.preprocessor)
            logger.info(f"Loaded preprocessor from {args.preprocessor}")
        except Exception as e:
            logger.warning(f"Could not load preprocessor: {e}")

    # Initialize alert manager
    alert_mgr = AlertManager(log_file=args.log_file, console_output=True, save_to_file=True)

    # Define alert callback
    def alert_callback(anomaly_info):
        """
        Callback function to handle anomaly detection alerts.

        Args:
            anomaly_info: Dictionary containing information about the detected anomaly
        """
        alert_mgr.generate_alert(
            anomaly_type='ml_detection',
            packet_info=anomaly_info,
            severity=AlertSeverity.HIGH
        )

    # Start real-time detection
    detector = RealtimeDetector(
        model=model,
        preprocessor=preprocessor,
        interface=args.interface
    )

    try:
        detector.start_detection(
            alert_callback=alert_callback,
            filter_rule=args.filter,
            duration=args.duration
        )
    except KeyboardInterrupt:
        logger.info("Stopping detection...")
    finally:
        # Print summary
        stats = detector.get_statistics()
        alert_mgr.print_summary()
        logger.info(f"Detection complete. Analyzed: {stats['total_analyzed']}, "
                   f"Anomalies: {stats['anomaly_count']}")


def offline_mode(args):
    """Run offline PCAP analysis"""
    logger.info("Starting offline PCAP analysis...")

    if not args.pcap:
        logger.error("PCAP file required for offline mode. Use --pcap <file.pcap>")
        sys.exit(1)

    # Load PCAP
    logger.info(f"Loading PCAP file: {args.pcap}")
    packets = PcapHandler.read_pcap(args.pcap)

    # Extract features
    logger.info("Extracting features...")
    feature_extractor = FeatureExtractor()
    packet_df = feature_extractor.extract_batch_features(packets)

    # Aggregate to flows
    flow_aggregator = FlowAggregator()
    flow_df = flow_aggregator.create_flow_features(packets)

    # Load model if provided
    anomaly_count = 0  # Initialize anomaly_count
    if args.model:
        try:
            model = safe_load(args.model, restricted=True)
            logger.info(f"Securely loaded model from {args.model}")

            # Load preprocessor
            preprocessor = None
            if args.preprocessor:
                preprocessor = FeaturePreprocessor.load(args.preprocessor)

            # Prepare features for model prediction
            if preprocessor:
                # Let the preprocessor handle feature selection and preparation
                X = preprocessor.transform(flow_df)
            else:
                # Fallback: use numeric features, excluding timestamps
                numeric_cols = flow_df.select_dtypes(include=['number']).columns.tolist()
                exclude_cols = ['timestamp', 'start_time', 'end_time']
                feature_cols = [c for c in numeric_cols if c not in exclude_cols]
                X = flow_df[feature_cols].fillna(0)

            # Predict anomalies
            predictions = model.predict(X)
            flow_df['anomaly'] = predictions

            anomaly_count = sum(predictions == -1) + sum(predictions == 1)
            logger.info(f"Detected {anomaly_count} anomalous flows out of {len(flow_df)}")

        except Exception as e:
            logger.error(f"Error in model prediction: {e}")
            flow_df['anomaly'] = 0
            anomaly_count = 0

    # Generate statistics
    traffic_stats = {
        'total_packets': len(packets),
        'total_bytes': packet_df['packet_size'].sum() if 'packet_size' in packet_df.columns else 0,
        'unique_ips': list(set(packet_df['src_ip'].dropna().tolist() + packet_df['dst_ip'].dropna().tolist())),
        'protocol_distribution': packet_df['protocol'].value_counts().to_dict() if 'protocol' in packet_df.columns else {},
        'top_src_ips': list(packet_df['src_ip'].value_counts().head(10).items()) if 'src_ip' in packet_df.columns else [],
        'top_dst_ips': list(packet_df['dst_ip'].value_counts().head(10).items()) if 'dst_ip' in packet_df.columns else []
    }

    # Generate visualizations
    viz = TrafficVisualizer()

    if 'protocol' in packet_df.columns:
        protocol_dist = packet_df['protocol'].value_counts().to_dict()
        viz.plot_protocol_distribution(protocol_dist)

    if 'packet_size' in packet_df.columns:
        viz.plot_packet_size_distribution(packet_df['packet_size'].dropna().tolist())

    # Generate HTML report
    analysis_results = {
        'period': f"PCAP File: {args.pcap}",
        'metrics': {
            'anomaly_count': anomaly_count,
            'anomaly_rate': anomaly_count / len(flow_df) if len(flow_df) > 0 else 0
        },
        'traffic_stats': traffic_stats,
        'alerts': []
    }

    output_file = args.output or 'reports/analysis_report.html'
    report_gen = HTMLReportGenerator()
    report_path = report_gen.generate_summary_report(analysis_results, output_file)

    logger.info(f"Analysis complete! Report saved to: {report_path}")


def train_mode(args):
    """Train a new model"""
    logger.info("Training new anomaly detection model...")

    if not args.data:
        logger.error("Training data required. Use --data <file.csv>")
        sys.exit(1)

    # Load training data
    import pandas as pd
    logger.info(f"Loading training data from {args.data}")
    df = pd.read_csv(args.data)

    # Prepare features
    preprocessor = FeaturePreprocessor()
    X = preprocessor.fit_transform(df)

    # Train model
    if args.model_type == 'isolation_forest':
        from models.unsupervised import IsolationForestDetector
        model = IsolationForestDetector(contamination=0.1, n_estimators=200)
    elif args.model_type == 'one_class_svm':
        from models.unsupervised import OneClassSVMDetector
        model = OneClassSVMDetector(nu=0.1)
    elif args.model_type == 'kmeans':
        from models.unsupervised import KMeansClusterer
        model = KMeansClusterer(n_clusters=5)

    logger.info(f"Training {args.model_type} model...")
    model.train(X)

    # Save model
    output_file = args.output or f'models/trained_models/{args.model_type}.pkl'
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    model.save(output_file)
    preprocessor.save(output_file.replace('.pkl', '_preprocessor.pkl'))

    logger.info(f"Model saved to: {output_file}")
    logger.info(f"Preprocessor saved to: {output_file.replace('.pkl', '_preprocessor.pkl')}")


def main():
    """Main entry point"""
    args = parse_arguments()

    if getattr(args, 'list_interfaces', False):
        interfaces = PacketSniffer.get_available_interfaces()
        if interfaces:
            try:
                auto_selected = PacketSniffer.resolve_interface(None)
            except ValueError:
                auto_selected = None

            print("Available interfaces (prioritized):")
            for iface in interfaces:
                marker = "*" if auto_selected and iface == auto_selected else " "
                print(f"  {marker} {iface}")

            if auto_selected:
                print("\n'*' indicates the interface that will be used by default.")
        else:
            print("No interfaces detected. Ensure you have the necessary permissions.")
        sys.exit(0)

    # Validate inputs based on mode
    try:
        is_valid, errors = InputValidator.validate_mode_requirements(args.mode, args)
        if not is_valid:
            logger.error("Input validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)

    try:
        if args.mode == 'realtime':
            realtime_mode(args)
        elif args.mode == 'offline':
            offline_mode(args)
        elif args.mode == 'train':
            train_mode(args)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
