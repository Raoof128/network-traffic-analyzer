"""
Feature Preprocessing Module
Normalize, clean, and prepare features for machine learning.

The original implementation relied on scikit-learn. To keep the project usable
in lightweight environments (including the execution sandbox used for tests),
we provide NumPy/Pandas based fallbacks when scikit-learn is unavailable.
"""

import logging
import pickle
from typing import Dict, List, Optional, Tuple

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
    from sklearn.decomposition import PCA  # type: ignore
    from sklearn.impute import SimpleImputer  # type: ignore
    from sklearn.preprocessing import (  # type: ignore
        LabelEncoder,
        MinMaxScaler,
        RobustScaler,
        StandardScaler,
    )
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - executed in minimal environments
    PCA = None  # type: ignore[assignment]
    SKLEARN_AVAILABLE = False

    class _BaseScaler:
        """Minimal scaler interface compatible with scikit-learn style API."""

        def __init__(self):
            self._columns: Optional[List[str]] = None
            self._is_dataframe = False

        def fit(self, X):
            self._is_dataframe = isinstance(X, pd.DataFrame)
            self._columns = list(X.columns) if self._is_dataframe else None
            array = np.asarray(X, dtype=float)
            if array.ndim == 1:
                array = array.reshape(-1, 1)
            self._fit_array(array)
            return self

        def transform(self, X):
            array = np.asarray(X, dtype=float)
            if array.ndim == 1:
                array = array.reshape(-1, 1)
            transformed = self._transform_array(array)
            if self._is_dataframe:
                return pd.DataFrame(transformed, columns=self._columns, index=getattr(X, "index", None))
            return transformed

        def fit_transform(self, X):
            return self.fit(X).transform(X)

        def _fit_array(self, array: np.ndarray):
            raise NotImplementedError

        def _transform_array(self, array: np.ndarray) -> np.ndarray:
            raise NotImplementedError

    class StandardScaler(_BaseScaler):  # type: ignore[override]
        def _fit_array(self, array: np.ndarray):
            self.mean_ = np.nanmean(array, axis=0)
            # Match scikit-learn behaviour (ddof=1) so sample std after scaling is ~1
            sample_count = array.shape[0]
            ddof = 1 if sample_count > 1 else 0
            self.scale_ = np.nanstd(array, axis=0, ddof=ddof)
            self.scale_ = np.nan_to_num(self.scale_, nan=1.0)
            self.scale_[self.scale_ == 0] = 1.0

        def _transform_array(self, array: np.ndarray) -> np.ndarray:
            return (array - self.mean_) / self.scale_

    class MinMaxScaler(_BaseScaler):  # type: ignore[override]
        def __init__(self, feature_range: Tuple[float, float] = (0, 1)):
            super().__init__()
            self.feature_range = feature_range

        def _fit_array(self, array: np.ndarray):
            self.data_min_ = np.nanmin(array, axis=0)
            self.data_max_ = np.nanmax(array, axis=0)
            range_width = self.data_max_ - self.data_min_
            range_width[range_width == 0] = 1.0
            self.scale_ = (self.feature_range[1] - self.feature_range[0]) / range_width
            self.min_ = self.feature_range[0] - self.data_min_ * self.scale_

        def _transform_array(self, array: np.ndarray) -> np.ndarray:
            return array * self.scale_ + self.min_

    class RobustScaler(_BaseScaler):  # type: ignore[override]
        def __init__(self, quantile_range: Tuple[float, float] = (25.0, 75.0)):
            super().__init__()
            self.quantile_range = quantile_range

        def _fit_array(self, array: np.ndarray):
            q_min, q_max = np.nanpercentile(array, self.quantile_range, axis=0)
            self.center_ = np.nanmedian(array, axis=0)
            iqr = q_max - q_min
            iqr[iqr == 0] = 1.0
            self.scale_ = iqr

        def _transform_array(self, array: np.ndarray) -> np.ndarray:
            return (array - self.center_) / self.scale_

    class SimpleImputer:  # type: ignore[override]
        """Simplified imputer supporting mean/median/constant strategies."""

        def __init__(self, strategy: str = "mean", fill_value: Optional[float] = None):
            self.strategy = strategy
            self.fill_value = fill_value
            self.statistics_: Optional[np.ndarray] = None
            self._columns: Optional[List[str]] = None
            self._is_dataframe = False

        def fit(self, X):
            self._is_dataframe = isinstance(X, pd.DataFrame)
            self._columns = list(X.columns) if self._is_dataframe else None
            array = np.asarray(X, dtype=float)
            if array.ndim == 1:
                array = array.reshape(-1, 1)

            if self.strategy == "mean":
                self.statistics_ = np.nanmean(array, axis=0)
            elif self.strategy == "median":
                self.statistics_ = np.nanmedian(array, axis=0)
            elif self.strategy == "constant":
                fill = 0.0 if self.fill_value is None else float(self.fill_value)
                self.statistics_ = np.full(array.shape[1], fill, dtype=float)
            else:
                raise ValueError(f"Unsupported strategy: {self.strategy}")

            self.statistics_ = np.nan_to_num(self.statistics_, nan=0.0)
            return self

        def transform(self, X):
            if self.statistics_ is None:
                raise RuntimeError("SimpleImputer must be fitted before transform.")

            array = np.asarray(X, dtype=float)
            if array.ndim == 1:
                array = array.reshape(-1, 1)

            inds = np.where(np.isnan(array))
            array[inds] = self.statistics_[inds[1]]

            if self._is_dataframe:
                return pd.DataFrame(array, columns=self._columns, index=getattr(X, "index", None))
            return array

    class LabelEncoder:  # type: ignore[override]
        """Lightweight label encoder compatible with sklearn's interface."""

        def __init__(self):
            self.classes_: Optional[np.ndarray] = None
            self._mapping: Dict[str, int] = {}

        def fit(self, y):
            values = pd.Series(y).dropna().astype(str).unique()
            self.classes_ = np.array(sorted(values))
            self._mapping = {cls: idx for idx, cls in enumerate(self.classes_)}
            return self

        def transform(self, y):
            if self.classes_ is None:
                raise RuntimeError("LabelEncoder must be fitted before transform.")
            return np.array([self._mapping[str(value)] for value in y], dtype=int)

        def fit_transform(self, y):
            return self.fit(y).transform(y)

        def inverse_transform(self, y):
            inverse = {idx: cls for cls, idx in self._mapping.items()}
            return np.array([inverse[int(value)] for value in y])

    class _UnavailablePCA:
        def __init__(self, *args, **kwargs):
            raise ImportError("PCA is unavailable because scikit-learn is not installed.")

    PCA = _UnavailablePCA  # type: ignore[assignment]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not SKLEARN_AVAILABLE:
    logger.info("scikit-learn not available; using lightweight preprocessing fallbacks.")


class FeaturePreprocessor:
    """Preprocess and normalize features for ML models"""

    def __init__(
        self,
        normalization: str = 'standard',
        missing_strategy: str = 'mean',
        variance_threshold: float = 0.01
    ):
        """
        Initialize feature preprocessor

        Args:
            normalization: Normalization method ('standard', 'minmax', 'robust')
            missing_strategy: Strategy for missing values ('mean', 'median', 'zero', 'drop')
            variance_threshold: Remove features with variance below this threshold
        """
        self.normalization = normalization
        self.missing_strategy = missing_strategy
        self.variance_threshold = variance_threshold

        self.scaler = None
        self.imputer = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.numeric_features: List[str] = []
        self.categorical_features: List[str] = []
        self.fitted = False
        
        # Store original features (before selection) for transform
        self.original_numeric_features: List[str] = []
        self.original_categorical_features: List[str] = []

    def _initialize_scaler(self):
        """Initialize the appropriate scaler"""
        if self.normalization == 'standard':
            self.scaler = StandardScaler()
        elif self.normalization == 'minmax':
            self.scaler = MinMaxScaler()
        elif self.normalization == 'robust':
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown normalization method: {self.normalization}")

    def _initialize_imputer(self):
        """Initialize the imputer for missing values"""
        if self.missing_strategy == 'mean':
            self.imputer = SimpleImputer(strategy='mean')
        elif self.missing_strategy == 'median':
            self.imputer = SimpleImputer(strategy='median')
        elif self.missing_strategy == 'zero':
            self.imputer = SimpleImputer(strategy='constant', fill_value=0)
        elif self.missing_strategy == 'drop':
            self.imputer = None
        else:
            raise ValueError(f"Unknown missing value strategy: {self.missing_strategy}")

    def identify_feature_types(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Identify numeric and categorical features

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (numeric_features, categorical_features)
        """
        numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Remove identifiers and timestamps from features
        exclude_features = ['flow_id', 'src_ip', 'dst_ip', 'timestamp', 'start_time', 'end_time']
        numeric_features = [f for f in numeric_features if f not in exclude_features]
        categorical_features = [f for f in categorical_features if f not in exclude_features]

        logger.info(f"Identified {len(numeric_features)} numeric and {len(categorical_features)} categorical features")

        return numeric_features, categorical_features

    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical features using label encoding

        Args:
            df: Input DataFrame
            fit: Whether to fit encoders (True for training, False for test/inference)

        Returns:
            DataFrame with encoded features
        """
        df = df.copy()

        for feature in self.categorical_features:
            if feature not in df.columns:
                continue

            if fit:
                self.label_encoders[feature] = LabelEncoder()
                # Handle NaN values
                mask = df[feature].notna()
                df.loc[mask, feature] = self.label_encoders[feature].fit_transform(df.loc[mask, feature].astype(str))
            else:
                if feature in self.label_encoders:
                    mask = df[feature].notna()
                    # Handle unknown categories
                    df.loc[mask, feature] = df.loc[mask, feature].apply(
                        lambda x: self.label_encoders[feature].transform([str(x)])[0]
                        if str(x) in self.label_encoders[feature].classes_
                        else -1
                    )

        return df

    def handle_missing_values(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Handle missing values in numeric features

        Args:
            df: Input DataFrame
            fit: Whether to fit imputer

        Returns:
            DataFrame with imputed values
        """
        if self.missing_strategy == 'drop':
            available_numeric = [f for f in self.original_numeric_features if f in df.columns]
            df = df.dropna(subset=available_numeric)
            logger.info(f"Dropped rows with missing values. Remaining rows: {len(df)}")
            return df

        df = df.copy()
        
        # Get available original numeric features for imputation
        available_numeric = [f for f in self.original_numeric_features if f in df.columns]
        
        if not available_numeric:
            return df

        if fit:
            # Fit on numpy array to avoid feature name checking
            self.imputer.fit(df[available_numeric].values)

        # Transform using numpy array and assign back
        df[available_numeric] = self.imputer.transform(df[available_numeric].values)

        return df

    def remove_low_variance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove features with low variance

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with low-variance features removed
        """
        variances = df[self.numeric_features].var()
        low_variance_features = variances[variances < self.variance_threshold].index.tolist()

        if low_variance_features:
            logger.info(f"Removing {len(low_variance_features)} low-variance features: {low_variance_features}")
            self.numeric_features = [f for f in self.numeric_features if f not in low_variance_features]
            df = df.drop(columns=low_variance_features)

        return df

    def normalize_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Normalize numeric features

        Args:
            df: Input DataFrame
            fit: Whether to fit scaler

        Returns:
            DataFrame with normalized features
        """
        df = df.copy()
        
        # Get available numeric features
        available_numeric = [f for f in self.numeric_features if f in df.columns]
        
        if not available_numeric:
            return df

        if fit:
            # Fit on numpy array to avoid feature name checking
            self.scaler.fit(df[available_numeric].values)

        # Transform using numpy array and assign back
        df[available_numeric] = self.scaler.transform(df[available_numeric].values)

        return df

    def detect_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect and remove outliers using z-score method

        Args:
            df: Input DataFrame
            threshold: Z-score threshold for outlier detection

        Returns:
            DataFrame with outliers removed
        """
        df = df.copy()
        z_scores = np.abs((df[self.numeric_features] - df[self.numeric_features].mean()) / df[self.numeric_features].std())
        outlier_mask = (z_scores < threshold).all(axis=1)

        outliers_count = (~outlier_mask).sum()
        logger.info(f"Detected {outliers_count} outlier rows (threshold={threshold})")

        return df[outlier_mask]

    def fit_transform(self, df: pd.DataFrame, remove_outliers: bool = True) -> pd.DataFrame:
        """
        Fit preprocessor and transform data

        Args:
            df: Input DataFrame
            remove_outliers: Whether to remove outliers

        Returns:
            Preprocessed DataFrame

        Example:
            >>> preprocessor = FeaturePreprocessor()
            >>> X_train_processed = preprocessor.fit_transform(X_train)
        """
        logger.info(f"Fitting preprocessor on {len(df)} samples")

        # Identify feature types and store original ones
        self.original_numeric_features, self.original_categorical_features = self.identify_feature_types(df)
        self.numeric_features, self.categorical_features = self.original_numeric_features.copy(), self.original_categorical_features.copy()
        self.feature_names = self.numeric_features + self.categorical_features

        # Encode categorical features
        if self.categorical_features:
            df = self.encode_categorical_features(df, fit=True)

        # Initialize and fit imputer
        if self.imputer is None:
            self._initialize_imputer()

        # Handle missing values using original feature set
        if self.imputer:
            if self.original_numeric_features:
                self.imputer.fit(df[self.original_numeric_features].values)
            df = self.handle_missing_values(df, fit=False)  # Apply imputation

        # Remove low variance features BEFORE fitting scaler
        df = self.remove_low_variance_features(df)

        # Initialize and fit scaler AFTER feature selection
        if self.scaler is None:
            self._initialize_scaler()

        # Normalize features
        df = self.normalize_features(df, fit=True)

        # Remove outliers (only during training)
        if remove_outliers:
            df = self.detect_outliers(df, threshold=3.0)

        self.fitted = True
        logger.info(f"Preprocessing complete. Output shape: {df.shape}")

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data using fitted preprocessor

        Args:
            df: Input DataFrame

        Returns:
            Preprocessed DataFrame

        Example:
            >>> X_test_processed = preprocessor.transform(X_test)
        """
        if not self.fitted:
            raise RuntimeError("Preprocessor must be fitted before transform")

        logger.info(f"Transforming {len(df)} samples")

        # Handle missing values using ORIGINAL features (before selection)
        if self.imputer:
            df = self.handle_missing_values(df, fit=False)

        # Encode categorical features
        if self.original_categorical_features:
            df = self.encode_categorical_features(df, fit=False)

        # NOW select only the features that were selected during training
        selected_features = self.numeric_features + self.categorical_features
        missing_features = [f for f in selected_features if f not in df.columns]
        if missing_features:
            logger.warning(f"Adding missing features with default values: {missing_features}")
            for feat in missing_features:
                df[feat] = 0

        # Keep only selected features
        df = df[selected_features].copy()

        # Normalize features (only the selected ones)
        df = self.normalize_features(df, fit=False)

        return df

    def save(self, filepath: str):
        """Save preprocessor to disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            safe_save(self, filepath)
            logger.info(f"Securely saved preprocessor to {filepath}")
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info(f"Saved preprocessor to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'FeaturePreprocessor':
        """Load preprocessor from disk using secure pickle"""
        if SECURE_PICKLE_AVAILABLE:
            preprocessor = safe_load(filepath, restricted=True)
            logger.info(f"Securely loaded preprocessor from {filepath}")
        else:
            with open(filepath, 'rb') as f:
                preprocessor = pickle.load(f)
            logger.info(f"Loaded preprocessor from {filepath}")
        return preprocessor


def normalize_features(df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
    """
    Convenience function to normalize features

    Args:
        df: Input DataFrame
        method: Normalization method

    Returns:
        Normalized DataFrame
    """
    preprocessor = FeaturePreprocessor(normalization=method)
    return preprocessor.fit_transform(df)
