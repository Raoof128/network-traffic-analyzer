"""
Supervised Classification Models
Random Forest, SVM, and ensemble methods for anomaly detection.

The implementations degrade gracefully when scikit-learn is unavailable by
using lightweight analytical fallbacks so that the project remains usable in
minimal environments.
"""

import logging
import pickle
import time
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

# Import secure pickle utilities
try:
    from utils.secure_pickle import safe_save, safe_load
    SECURE_PICKLE_AVAILABLE = True
except ImportError:
    SECURE_PICKLE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Secure pickle utilities not available, falling back to standard pickle")

try:  # pragma: no cover - optional dependency
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier  # type: ignore
    from sklearn.linear_model import LogisticRegression  # type: ignore
    from sklearn.svm import SVC  # type: ignore
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - executed in minimal environments
    RandomForestClassifier = None  # type: ignore[assignment]
    VotingClassifier = None  # type: ignore[assignment]
    LogisticRegression = None  # type: ignore[assignment]
    SVC = None  # type: ignore[assignment]
    SKLEARN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not SKLEARN_AVAILABLE:
    logger.info("scikit-learn not available; supervised models falling back to analytical classifiers.")


class _GaussianNBClassifier:
    """Lightweight Gaussian Naive Bayes used as a supervised fallback."""

    def __init__(self):
        self.classes_: Optional[np.ndarray] = None
        self.class_log_prior_: Optional[np.ndarray] = None
        self.theta_: Optional[np.ndarray] = None
        self.var_: Optional[np.ndarray] = None
        self.feature_importances_: Optional[np.ndarray] = None

    def fit(self, X, y):
        array = np.asarray(X, dtype=float)
        labels = np.asarray(y)
        classes = np.unique(labels)
        if classes.size == 0:
            raise ValueError("At least one class is required.")

        means = []
        variances = []
        log_prior = []
        for cls in classes:
            cls_mask = labels == cls
            cls_samples = array[cls_mask]
            if cls_samples.size == 0:
                raise ValueError("Each class must have at least one sample.")
            means.append(cls_samples.mean(axis=0))
            var = cls_samples.var(axis=0)
            var[var == 0] = 1e-9
            variances.append(var)
            log_prior.append(np.log(cls_samples.shape[0] / array.shape[0]))

        self.classes_ = classes
        self.theta_ = np.vstack(means)
        self.var_ = np.vstack(variances)
        self.class_log_prior_ = np.array(log_prior)

        # Approximate feature importance by absolute difference between class means.
        if classes.size > 1:
            diff = np.abs(self.theta_[1] - self.theta_[0])
            total = diff.sum()
            self.feature_importances_ = diff / total if total != 0 else np.zeros_like(diff)
        else:
            self.feature_importances_ = np.zeros(array.shape[1])
        return self

    def _log_likelihood(self, array: np.ndarray) -> np.ndarray:
        if self.theta_ is None or self.var_ is None or self.class_log_prior_ is None or self.classes_ is None:
            raise RuntimeError("Classifier not fitted.")
        log_prob = []
        for idx in range(len(self.classes_)):
            mean = self.theta_[idx]
            var = self.var_[idx]
            likelihood = -0.5 * (np.log(2 * np.pi * var) + ((array - mean) ** 2) / var)
            log_prob.append(self.class_log_prior_[idx] + likelihood.sum(axis=1))
        return np.vstack(log_prob).T

    def predict_proba(self, X):
        array = np.asarray(X, dtype=float)
        logits = self._log_likelihood(array)
        max_log = np.max(logits, axis=1, keepdims=True)
        exp = np.exp(logits - max_log)
        probs = exp / exp.sum(axis=1, keepdims=True)
        return probs

    def predict(self, X):
        probs = self.predict_proba(X)
        indices = np.argmax(probs, axis=1)
        if self.classes_ is None:
            raise RuntimeError("Classifier not fitted.")
        return self.classes_[indices]


class RandomForestDetector:
    """Random Forest classifier for anomaly detection"""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        random_state: int = 42
    ):
        """
        Initialize Random Forest detector

        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees (None = unlimited)
            min_samples_split: Minimum samples required to split node
            random_state: Random seed

        Example:
            >>> detector = RandomForestDetector(n_estimators=200)
            >>> detector.train(X_train, y_train)
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state

        if SKLEARN_AVAILABLE:
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                random_state=random_state,
                n_jobs=-1
            )
        else:
            self.model = _GaussianNBClassifier()

        self.trained = False
        self.training_time = 0
        self.feature_importances_ = None

    def train(self, X: pd.DataFrame, y: np.ndarray) -> 'RandomForestDetector':
        """
        Train the Random Forest model

        Args:
            X: Training features
            y: Training labels (0 = normal, 1 = anomaly)

        Returns:
            Self for method chaining
        """
        logger.info(f"Training Random Forest on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X, y)

        self.training_time = time.time() - start_time
        self.feature_importances_ = getattr(
            self.model,
            'feature_importances_',
            np.zeros(X.shape[1])
        )
        self.trained = True

        logger.info(f"Training complete in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Args:
            X: Features to predict

        Returns:
            Array of predictions (0 = normal, 1 = anomaly)
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = self.model.predict(X)
        anomaly_count = np.sum(predictions == 1)
        logger.info(
            f"Detected {anomaly_count} anomalies out of {len(X)} samples "
            f"({(anomaly_count/len(X))*100:.2f}%)"
        )

        return predictions

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities

        Args:
            X: Features

        Returns:
            Array of probabilities [normal_prob, anomaly_prob]
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)

        probs = self.model.predict_proba(X)  # type: ignore[attr-defined]
        return probs

    def get_feature_importance(self, feature_names: list) -> pd.DataFrame:
        """
        Get feature importance scores

        Args:
            feature_names: List of feature names

        Returns:
            DataFrame with feature importance scores
        """
        if not self.trained:
            raise RuntimeError("Model must be trained first")

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': self.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved Random Forest model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved Random Forest model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'RandomForestDetector':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded Random Forest model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded Random Forest model from {filepath}")
        return model


class SVMDetector:
    """Support Vector Machine classifier for anomaly detection"""

    def __init__(
        self,
        kernel: str = 'rbf',
        C: float = 1.0,
        gamma: str = 'scale',
        probability: bool = True,
        random_state: int = 42
    ):
        """
        Initialize SVM detector

        Args:
            kernel: Kernel type ('linear', 'poly', 'rbf', 'sigmoid')
            C: Regularization parameter
            gamma: Kernel coefficient
            probability: Enable probability estimates
            random_state: Random seed
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.probability = probability
        self.random_state = random_state

        if SKLEARN_AVAILABLE:
            self.model = SVC(
                kernel=kernel,
                C=C,
                gamma=gamma,
                probability=probability,
                random_state=random_state
            )
        else:
            self.model = _GaussianNBClassifier()

        self.trained = False
        self.training_time = 0

    def train(self, X: pd.DataFrame, y: np.ndarray) -> 'SVMDetector':
        """Train the SVM model"""
        logger.info(f"Training SVM on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X, y)

        self.training_time = time.time() - start_time
        self.trained = True

        logger.info(f"Training complete in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Returns:
            Array of predictions (0 = normal, 1 = anomaly)
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = self.model.predict(X)
        anomaly_count = np.sum(predictions == 1)
        logger.info(
            f"Detected {anomaly_count} anomalies out of {len(X)} samples "
            f"({(anomaly_count/len(X))*100:.2f}%)"
        )

        return predictions

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        if SKLEARN_AVAILABLE and not self.probability:
            raise RuntimeError("Probability not enabled for this model")

        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)

        probs = self.model.predict_proba(X)  # type: ignore[attr-defined]
        return probs

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved SVM model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved SVM model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'SVMDetector':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded SVM model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded SVM model from {filepath}")
        return model


class EnsembleDetector:
    """Ensemble of multiple detectors for improved accuracy"""

    def __init__(
        self,
        voting: str = 'soft',
        random_state: int = 42
    ):
        """
        Initialize ensemble detector

        Args:
            voting: Voting strategy ('hard' or 'soft')
            random_state: Random seed
        """
        self.voting = voting
        self.random_state = random_state

        if SKLEARN_AVAILABLE:
            estimators = [
                ('rf', RandomForestClassifier(n_estimators=100, random_state=random_state, n_jobs=-1)),
                ('svm', SVC(kernel='rbf', probability=True, random_state=random_state)),
                ('lr', LogisticRegression(random_state=random_state, max_iter=1000))
            ]

            self.model = VotingClassifier(
                estimators=estimators,
                voting=voting,
                n_jobs=-1
            )
        else:
            # Fallback to a single analytical classifier.
            self.model = _GaussianNBClassifier()

        self.trained = False
        self.training_time = 0

    def train(self, X: pd.DataFrame, y: np.ndarray) -> 'EnsembleDetector':
        """Train the ensemble model"""
        logger.info(f"Training Ensemble model on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X, y)

        self.training_time = time.time() - start_time
        self.trained = True

        logger.info(f"Ensemble training complete in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict anomalies"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = self.model.predict(X)
        anomaly_count = np.sum(predictions == 1)
        logger.info(
            f"Detected {anomaly_count} anomalies out of {len(X)} samples "
            f"({(anomaly_count/len(X))*100:.2f}%)"
        )

        return predictions

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)

        probs = self.model.predict_proba(X)  # type: ignore[attr-defined]
        return probs

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved Ensemble model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved Ensemble model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'EnsembleDetector':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded Ensemble model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded Ensemble model from {filepath}")
        return model


def train_supervised_model(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    model_type: str = 'random_forest',
    **kwargs
):
    """
    Convenience function to train supervised model

    Args:
        X_train: Training features
        y_train: Training labels
        model_type: Model type ('random_forest', 'svm', 'ensemble')
        **kwargs: Additional model parameters

    Returns:
        Trained detector
    """
    if model_type == 'random_forest':
        detector = RandomForestDetector(**kwargs)
    elif model_type == 'svm':
        detector = SVMDetector(**kwargs)
    elif model_type == 'ensemble':
        detector = EnsembleDetector(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    detector.train(X_train, y_train)
    return detector

