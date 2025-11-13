#!/usr/bin/env python3
"""
Model Training Script
Train and evaluate anomaly detection models
"""

import argparse
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

from features.preprocessor import FeaturePreprocessor
from models.unsupervised import IsolationForestDetector, OneClassSVMDetector, KMeansClusterer
from models.supervised import RandomForestDetector, SVMDetector, EnsembleDetector
from models.evaluator import ModelEvaluator
from utils.validators import InputValidator, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Train anomaly detection models')

    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Path to training data CSV file'
    )

    parser.add_argument(
        '--model-type',
        type=str,
        required=True,
        choices=['isolation_forest', 'one_class_svm', 'kmeans', 'random_forest', 'svm', 'ensemble'],
        help='Type of model to train'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='models/trained_models',
        help='Output directory for trained models'
    )

    parser.add_argument(
        '--label-column',
        type=str,
        help='Column name containing labels (for supervised models)'
    )

    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set size (default: 0.2)'
    )

    parser.add_argument(
        '--contamination',
        type=float,
        default=0.1,
        help='Expected contamination rate for unsupervised models (default: 0.1)'
    )

    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Number of estimators for ensemble models (default: 100)'
    )

    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Evaluate model on test set (requires labels)'
    )

    return parser.parse_args()


def load_and_prepare_data(file_path: str, label_column: str = None, test_size: float = 0.2):
    """Load and prepare training data"""
    logger.info(f"Loading data from {file_path}")

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} features")

        # Separate features and labels
        if label_column and label_column in df.columns:
            y = df[label_column].values
            X = df.drop(columns=[label_column])
            logger.info(f"Using '{label_column}' as label column")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )

            logger.info(f"Train set: {len(X_train)} samples, Test set: {len(X_test)} samples")
            return X_train, X_test, y_train, y_test

        else:
            # No labels - unsupervised learning
            X_train, X_test = train_test_split(df, test_size=test_size, random_state=42)
            logger.info(f"Train set: {len(X_train)} samples, Test set: {len(X_test)} samples")
            return X_train, X_test, None, None

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        sys.exit(1)


def train_unsupervised_model(model_type: str, X_train: pd.DataFrame, args):
    """Train unsupervised model"""
    logger.info(f"Training {model_type} model...")

    if model_type == 'isolation_forest':
        model = IsolationForestDetector(
            contamination=args.contamination,
            n_estimators=args.n_estimators
        )
    elif model_type == 'one_class_svm':
        model = OneClassSVMDetector(nu=args.contamination)
    elif model_type == 'kmeans':
        model = KMeansClusterer(n_clusters=5, anomaly_percentile=95)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Preprocess data
    preprocessor = FeaturePreprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)

    # Train model
    model.train(X_train_processed)

    return model, preprocessor


def train_supervised_model(model_type: str, X_train: pd.DataFrame, y_train: np.ndarray, args):
    """Train supervised model"""
    logger.info(f"Training {model_type} model...")

    if model_type == 'random_forest':
        model = RandomForestDetector(
            n_estimators=args.n_estimators,
            max_depth=None,
            random_state=42
        )
    elif model_type == 'svm':
        model = SVMDetector(kernel='rbf', C=1.0, random_state=42)
    elif model_type == 'ensemble':
        model = EnsembleDetector(voting='soft', random_state=42)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Preprocess data
    preprocessor = FeaturePreprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)

    # Train model
    model.train(X_train_processed, y_train)

    return model, preprocessor


def evaluate_model(model, preprocessor, X_test, y_test, model_name: str):
    """Evaluate model on test set"""
    logger.info(f"Evaluating {model_name} on test set...")

    # Preprocess test data
    X_test_processed = preprocessor.transform(X_test)

    # Evaluate
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_model(model, X_test_processed, y_test, model_name)

    # Plot confusion matrix
    try:
        evaluator.plot_confusion_matrix(y_test, results['predictions'],
                                       save_path=f'visualization/plots/{model_name}_confusion_matrix.png')
    except:
        pass

    return results


def save_model(model, preprocessor, output_dir: str, model_type: str):
    """Save trained model and preprocessor"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    model_path = Path(output_dir) / f"{model_type}.pkl"
    preprocessor_path = Path(output_dir) / f"{model_type}_preprocessor.pkl"

    model.save(str(model_path))
    preprocessor.save(str(preprocessor_path))

    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Preprocessor saved to: {preprocessor_path}")

    return model_path, preprocessor_path


def main():
    """Main training pipeline"""
    args = parse_arguments()

    # Validate input data file
    try:
        InputValidator.validate_csv_file(args.data)
    except ValidationError as e:
        logger.error(f"Data file validation failed: {e}")
        sys.exit(1)

    # Validate output directory
    try:
        InputValidator.validate_output_path(args.output, create_dirs=True)
    except ValidationError as e:
        logger.error(f"Output path validation failed: {e}")
        sys.exit(1)

    # Load data
    if args.model_type in ['random_forest', 'svm', 'ensemble']:
        # Supervised models require labels
        if not args.label_column:
            logger.error("Supervised models require --label-column")
            sys.exit(1)

        X_train, X_test, y_train, y_test = load_and_prepare_data(
            args.data, args.label_column, args.test_size
        )

        # Train model
        model, preprocessor = train_supervised_model(args.model_type, X_train, y_train, args)

    else:
        # Unsupervised models
        X_train, X_test, y_train, y_test = load_and_prepare_data(
            args.data, args.label_column, args.test_size
        )

        # Train model
        model, preprocessor = train_unsupervised_model(args.model_type, X_train, args)

    # Save model
    model_path, preprocessor_path = save_model(model, preprocessor, args.output, args.model_type)

    # Evaluate if requested and labels available
    if args.evaluate and y_test is not None:
        results = evaluate_model(model, preprocessor, X_test, y_test, args.model_type)

        logger.info("\n" + "="*60)
        logger.info("TRAINING COMPLETE")
        logger.info("="*60)
        logger.info(f"Model Type: {args.model_type}")
        logger.info(f"Model Path: {model_path}")
        logger.info(f"Preprocessor Path: {preprocessor_path}")
        logger.info(f"Accuracy: {results['metrics']['accuracy']:.3f}")
        logger.info(f"Precision: {results['metrics']['precision']:.3f}")
        logger.info(f"Recall: {results['metrics']['recall']:.3f}")
        logger.info(f"F1-Score: {results['metrics']['f1_score']:.3f}")
        logger.info("="*60)

    else:
        logger.info("\n" + "="*60)
        logger.info("TRAINING COMPLETE")
        logger.info("="*60)
        logger.info(f"Model Type: {args.model_type}")
        logger.info(f"Model Path: {model_path}")
        logger.info(f"Preprocessor Path: {preprocessor_path}")
        logger.info("="*60)


if __name__ == '__main__':
    main()
