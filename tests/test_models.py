"""
Unit tests for ML models
"""

import pytest
import pandas as pd
import numpy as np
from models.unsupervised import IsolationForestDetector, OneClassSVMDetector, KMeansClusterer
from models.supervised import RandomForestDetector
from models.evaluator import ModelEvaluator


class TestIsolationForest:
    """Test Isolation Forest model"""

    def test_initialization(self):
        """Test model initialization"""
        model = IsolationForestDetector(contamination=0.1, n_estimators=50)
        assert model.contamination == 0.1
        assert model.n_estimators == 50
        assert not model.trained

    def test_train_and_predict(self):
        """Test training and prediction"""
        # Create sample data
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })

        model = IsolationForestDetector(contamination=0.1)
        model.train(X)

        assert model.trained

        # Predict
        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert set(predictions).issubset({-1, 1})

    def test_save_and_load(self, tmp_path):
        """Test saving and loading model"""
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50)
        })

        model = IsolationForestDetector()
        model.train(X)

        # Save
        model_file = tmp_path / "test_model.pkl"
        model.save(str(model_file))

        # Load
        loaded_model = IsolationForestDetector.load(str(model_file))
        assert loaded_model.trained

        # Verify predictions match
        pred_original = model.predict(X)
        pred_loaded = loaded_model.predict(X)
        assert all(pred_original == pred_loaded)


class TestRandomForest:
    """Test Random Forest model"""

    def test_train_and_predict(self):
        """Test training supervised model"""
        # Create sample data
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        y = np.random.randint(0, 2, 100)

        model = RandomForestDetector(n_estimators=50)
        model.train(X, y)

        assert model.trained

        # Predict
        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert set(predictions).issubset({0, 1})

    def test_predict_proba(self):
        """Test probability predictions"""
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50)
        })
        y = np.random.randint(0, 2, 50)

        model = RandomForestDetector()
        model.train(X, y)

        proba = model.predict_proba(X)
        assert proba.shape == (len(X), 2)
        assert np.allclose(proba.sum(axis=1), 1.0)


class TestModelEvaluator:
    """Test model evaluation"""

    def test_calculate_metrics(self):
        """Test metric calculation"""
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 0, 1, 0, 0, 1, 1, 1])

        metrics = ModelEvaluator.calculate_metrics(y_true, y_pred)

        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 0 <= metrics['accuracy'] <= 1

    def test_evaluate_model(self):
        """Test full model evaluation"""
        # Create simple model
        X_train = pd.DataFrame(np.random.randn(100, 2))
        y_train = np.random.randint(0, 2, 100)

        X_test = pd.DataFrame(np.random.randn(50, 2))
        y_test = np.random.randint(0, 2, 50)

        model = RandomForestDetector(n_estimators=10)
        model.train(X_train, y_train)

        # Evaluate
        results = ModelEvaluator.evaluate_model(model, X_test, y_test, "TestModel")

        assert 'metrics' in results
        assert 'predictions' in results
        assert len(results['predictions']) == len(y_test)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
