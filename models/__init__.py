"""Machine learning models for anomaly detection"""

from .unsupervised import (
    IsolationForestDetector,
    OneClassSVMDetector,
    KMeansClusterer,
    train_isolation_forest,
    detect_anomalies
)
from .supervised import (
    RandomForestDetector,
    SVMDetector,
    EnsembleDetector,
    train_supervised_model
)
from .evaluator import (
    ModelEvaluator,
    evaluate_model
)

__all__ = [
    # Unsupervised
    'IsolationForestDetector',
    'OneClassSVMDetector',
    'KMeansClusterer',
    'train_isolation_forest',
    'detect_anomalies',
    # Supervised
    'RandomForestDetector',
    'SVMDetector',
    'EnsembleDetector',
    'train_supervised_model',
    # Evaluation
    'ModelEvaluator',
    'evaluate_model'
]
