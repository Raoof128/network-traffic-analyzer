"""
Unsupervised Anomaly Detection Models
Isolation Forest, One-Class SVM, and K-Means clustering.

The original implementations depended on scikit-learn. This module now
provides lightweight fallbacks so the project remains functional when
scikit-learn is unavailable (as is the case in the execution sandbox used for
tests).
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
    logger.warning("Secure pickle utilities not available, falling back to standard pickle")

try:  # pragma: no cover - optional dependency
    from sklearn.cluster import KMeans  # type: ignore
    from sklearn.ensemble import IsolationForest  # type: ignore
    from sklearn.svm import OneClassSVM  # type: ignore
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - executed in minimal environments
    IsolationForest = None  # type: ignore[assignment]
    OneClassSVM = None  # type: ignore[assignment]
    KMeans = None  # type: ignore[assignment]
    SKLEARN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not SKLEARN_AVAILABLE:
    logger.info("scikit-learn not available; using analytical fallbacks for unsupervised models.")


class _FallbackIsolationForest:
    """Simple distance-based anomaly detector mimicking Isolation Forest behaviour."""

    def __init__(self, contamination: float = 0.1, random_state: int = 42, **_):
        self.contamination = max(0.0, min(contamination, 0.5))
        self.random_state = random_state
        self._mean: Optional[np.ndarray] = None
        self._std: Optional[np.ndarray] = None
        self._threshold: float = np.inf

    def fit(self, X: pd.DataFrame):
        array = np.asarray(X, dtype=float)
        if array.ndim == 1:
            array = array.reshape(-1, 1)
        self._mean = np.nanmean(array, axis=0)
        self._std = np.nanstd(array, axis=0)
        self._std[self._std == 0] = 1.0

        scores = self._score_array(array)
        if self.contamination <= 0 or len(scores) == 0:
            self._threshold = np.inf
        else:
            quantile = max(0.0, min(1.0, 1 - self.contamination))
            self._threshold = float(np.quantile(scores, quantile))
        return self

    def _score_array(self, array: np.ndarray) -> np.ndarray:
        if self._mean is None or self._std is None:
            raise RuntimeError("Fallback IsolationForest not fitted.")
        z_scores = (array - self._mean) / self._std
        return np.sum(z_scores**2, axis=1)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        scores = self._score_array(np.asarray(X, dtype=float))
        predictions = np.ones(len(scores), dtype=int)
        predictions[scores > self._threshold] = -1
        return predictions

    def score_samples(self, X: pd.DataFrame) -> np.ndarray:
        scores = self._score_array(np.asarray(X, dtype=float))
        return -scores


class _FallbackOneClassSVM(_FallbackIsolationForest):
    """Fallback that mirrors One-Class SVM interface using z-score distances."""

    def __init__(self, nu: float = 0.1, **kwargs):
        super().__init__(contamination=nu, **kwargs)

    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        return self.score_samples(X)


class _FallbackKMeans:
    """Compact K-Means implementation using Lloyd's algorithm."""

    def __init__(self, n_clusters: int = 5, random_state: int = 42, max_iter: int = 100):
        if n_clusters <= 0:
            raise ValueError("n_clusters must be positive.")
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.max_iter = max_iter
        self.cluster_centers_: Optional[np.ndarray] = None

    def fit(self, X: pd.DataFrame):
        array = np.asarray(X, dtype=float)
        if array.shape[0] < self.n_clusters:
            raise ValueError("Number of samples must be >= n_clusters.")
        rng = np.random.default_rng(self.random_state)
        indices = rng.choice(array.shape[0], size=self.n_clusters, replace=False)
        centroids = array[indices]

        for _ in range(self.max_iter):
            distances = self._compute_distances(array, centroids)
            labels = np.argmin(distances, axis=1)
            new_centroids = np.empty_like(centroids)
            for idx in range(self.n_clusters):
                cluster_points = array[labels == idx]
                if len(cluster_points) == 0:
                    new_centroids[idx] = centroids[idx]
                else:
                    new_centroids[idx] = cluster_points.mean(axis=0)
            if np.allclose(new_centroids, centroids, rtol=1e-4, atol=1e-6):
                centroids = new_centroids
                break
            centroids = new_centroids

        self.cluster_centers_ = centroids
        return self

    @staticmethod
    def _compute_distances(array: np.ndarray, centroids: np.ndarray) -> np.ndarray:
        diff = array[:, np.newaxis, :] - centroids[np.newaxis, :, :]
        return np.linalg.norm(diff, axis=2)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if self.cluster_centers_ is None:
            raise RuntimeError("Fallback KMeans must be fitted before transform.")
        array = np.asarray(X, dtype=float)
        return self._compute_distances(array, self.cluster_centers_)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        distances = self.transform(X)
        return np.argmin(distances, axis=1)


class IsolationForestDetector:
    """Isolation Forest anomaly detector"""

    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: int = 256,
        random_state: int = 42
    ):
        """
        Initialize Isolation Forest detector

        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
            n_estimators: Number of trees in the forest
            max_samples: Number of samples to draw for each tree
            random_state: Random seed

        Example:
            >>> detector = IsolationForestDetector(contamination=0.1)
            >>> detector.train(X_train)
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state

        if SKLEARN_AVAILABLE:
            self.model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                max_samples=max_samples,
                random_state=random_state,
                n_jobs=-1,  # Use all CPU cores
            )
        else:
            self.model = _FallbackIsolationForest(
                contamination=contamination,
                random_state=random_state,
            )

        self.trained = False
        self.training_time = 0

    def train(self, X: pd.DataFrame) -> 'IsolationForestDetector':
        """
        Train the Isolation Forest model

        Args:
            X: Training features

        Returns:
            Self for method chaining
        """
        logger.info(f"Training Isolation Forest on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X)

        self.training_time = time.time() - start_time
        self.trained = True

        logger.info(f"Training complete in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Args:
            X: Features to predict

        Returns:
            Array of predictions (1 = normal, -1 = anomaly)
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = self.model.predict(X)
        anomaly_count = np.sum(predictions == -1)
        logger.info(f"Detected {anomaly_count} anomalies out of {len(X)} samples ({anomaly_count/len(X)*100:.2f}%)")

        return predictions

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly scores (lower = more anomalous)

        Args:
            X: Features

        Returns:
            Array of anomaly scores
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        scores = self.model.score_samples(X)
        return scores

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved Isolation Forest model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved Isolation Forest model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'IsolationForestDetector':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded Isolation Forest model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded Isolation Forest model from {filepath}")
        return model


class OneClassSVMDetector:
    """One-Class SVM anomaly detector"""

    def __init__(
        self,
        kernel: str = 'rbf',
        gamma: str = 'scale',
        nu: float = 0.1
    ):
        """
        Initialize One-Class SVM detector

        Args:
            kernel: Kernel type ('linear', 'poly', 'rbf', 'sigmoid')
            gamma: Kernel coefficient
            nu: Upper bound on fraction of anomalies (similar to contamination)

        Example:
            >>> detector = OneClassSVMDetector(nu=0.1)
            >>> detector.train(X_train)
        """
        self.kernel = kernel
        self.gamma = gamma
        self.nu = nu

        if SKLEARN_AVAILABLE:
            self.model = OneClassSVM(
                kernel=kernel,
                gamma=gamma,
                nu=nu
            )
        else:
            self.model = _FallbackOneClassSVM(
                nu=nu,
                kernel=kernel,
                gamma=gamma,
                random_state=42,
            )

        self.trained = False
        self.training_time = 0

    def train(self, X: pd.DataFrame) -> 'OneClassSVMDetector':
        """Train the One-Class SVM model"""
        logger.info(f"Training One-Class SVM on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X)

        self.training_time = time.time() - start_time
        self.trained = True

        logger.info(f"Training complete in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Returns:
            Array of predictions (1 = normal, -1 = anomaly)
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = self.model.predict(X)
        anomaly_count = np.sum(predictions == -1)
        logger.info(f"Detected {anomaly_count} anomalies out of {len(X)} samples ({anomaly_count/len(X)*100:.2f}%)")

        return predictions

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Get decision function scores"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        scores = self.model.decision_function(X)
        return scores

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved One-Class SVM model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved One-Class SVM model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'OneClassSVMDetector':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded One-Class SVM model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded One-Class SVM model from {filepath}")
        return model


class KMeansClusterer:
    """K-Means clustering for baseline behavior identification"""

    def __init__(
        self,
        n_clusters: int = 5,
        anomaly_percentile: float = 95,
        random_state: int = 42
    ):
        """
        Initialize K-Means clusterer

        Args:
            n_clusters: Number of clusters
            anomaly_percentile: Percentile threshold for anomaly distance
            random_state: Random seed

        Example:
            >>> clusterer = KMeansClusterer(n_clusters=5)
            >>> clusterer.train(X_train)
        """
        self.n_clusters = n_clusters
        self.anomaly_percentile = anomaly_percentile
        self.random_state = random_state

        if SKLEARN_AVAILABLE:
            self.model = KMeans(
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=10
            )
        else:
            self.model = _FallbackKMeans(
                n_clusters=n_clusters,
                random_state=random_state
            )

        self.trained = False
        self.anomaly_threshold = None
        self.training_time = 0

    def train(self, X: pd.DataFrame) -> 'KMeansClusterer':
        """Train the K-Means model"""
        logger.info(f"Training K-Means with {self.n_clusters} clusters on {len(X)} samples...")
        start_time = time.time()

        self.model.fit(X)

        # Calculate anomaly threshold based on training data distances
        distances = self.model.transform(X).min(axis=1)
        self.anomaly_threshold = np.percentile(distances, self.anomaly_percentile)

        self.training_time = time.time() - start_time
        self.trained = True

        logger.info(f"Training complete in {self.training_time:.2f} seconds")
        logger.info(f"Anomaly threshold: {self.anomaly_threshold:.4f}")

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies based on distance to nearest cluster

        Returns:
            Array of predictions (1 = normal, -1 = anomaly)
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        distances = self.model.transform(X).min(axis=1)
        predictions = np.where(distances > self.anomaly_threshold, -1, 1)

        anomaly_count = np.sum(predictions == -1)
        logger.info(f"Detected {anomaly_count} anomalies out of {len(X)} samples ({anomaly_count/len(X)*100:.2f}%)")

        return predictions

    def get_cluster_labels(self, X: pd.DataFrame) -> np.ndarray:
        """Get cluster assignments"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        return self.model.predict(X)

    def get_distances(self, X: pd.DataFrame) -> np.ndarray:
        """Get distances to nearest cluster center"""
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        return self.model.transform(X).min(axis=1)

    def save(self, filepath: str):
        """Save model to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved K-Means model to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved K-Means model to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'KMeansClusterer':
        """Load model from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            model = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded K-Means model from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded K-Means model from {filepath}")
        return model


def train_isolation_forest(
    X: pd.DataFrame,
    contamination: float = 0.1,
    **kwargs
) -> IsolationForestDetector:
    """
    Convenience function to train Isolation Forest

    Args:
        X: Training features
        contamination: Expected anomaly rate
        **kwargs: Additional model parameters

    Returns:
        Trained detector
    """
    detector = IsolationForestDetector(contamination=contamination, **kwargs)
    detector.train(X)
    return detector


def detect_anomalies(model, X: pd.DataFrame) -> np.ndarray:
    """
    Convenience function to detect anomalies

    Args:
        model: Trained anomaly detection model
        X: Features to predict

    Returns:
        Array of predictions (1 = normal, -1 = anomaly)
    """
    return model.predict(X)
