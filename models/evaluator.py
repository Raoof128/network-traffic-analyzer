"""
Model Evaluation Module
Calculate metrics and evaluate anomaly detection models.

Provides fallbacks for common metrics when scikit-learn is unavailable.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

try:  # pragma: no cover - optional dependency
    import matplotlib.pyplot as plt  # type: ignore
    HAS_MPL = True
except ImportError:  # pragma: no cover - executed in minimal environments
    plt = None  # type: ignore[assignment]
    HAS_MPL = False

try:  # pragma: no cover - optional dependency
    import seaborn as sns  # type: ignore
    HAS_SEABORN = True
except ImportError:  # pragma: no cover - executed in minimal environments
    sns = None  # type: ignore[assignment]
    HAS_SEABORN = False

try:  # pragma: no cover - optional dependency
    from sklearn.metrics import (  # type: ignore
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
        roc_curve,
    )
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - executed in minimal environments
    SKLEARN_AVAILABLE = False

    def accuracy_score(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        return float(np.mean(y_true == y_pred)) if len(y_true) else 0.0

    def precision_score(y_true, y_pred, zero_division=0):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        positives = np.sum(y_pred == 1)
        if positives == 0:
            return float(zero_division)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        return float(tp / positives)

    def recall_score(y_true, y_pred, zero_division=0):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        actual = np.sum(y_true == 1)
        if actual == 0:
            return float(zero_division)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        return float(tp / actual)

    def f1_score(y_true, y_pred, zero_division=0):
        precision = precision_score(y_true, y_pred, zero_division=zero_division)
        recall = recall_score(y_true, y_pred, zero_division=zero_division)
        if precision + recall == 0:
            return float(zero_division)
        return float(2 * precision * recall / (precision + recall))

    def confusion_matrix(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        tp = np.sum((y_true == 1) & (y_pred == 1))
        return np.array([[tn, fp], [fn, tp]], dtype=int)

    def classification_report(y_true, y_pred, target_names=None, zero_division=0):
        labels = [0, 1]
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        names = target_names or ['0', '1']
        lines = ["              precision    recall  f1-score   support"]
        total_support = len(y_true)

        for label, name in zip(labels, names):
            mask = y_true == label
            support = int(mask.sum())
            pred_mask = y_pred == label
            tp = int(np.sum(mask & pred_mask))
            precision = tp / pred_mask.sum() if pred_mask.sum() else float(zero_division)
            recall = tp / support if support else float(zero_division)
            f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
            lines.append(f"{name:>12} {precision:10.2f} {recall:8.2f} {f1:9.2f} {support:10d}")

        accuracy = accuracy_score(y_true, y_pred)
        lines.append("")
        lines.append(f"   accuracy {accuracy:10.2f} {total_support:10d}")
        return "\n".join(lines)

    def roc_curve(y_true, y_scores):
        y_true = np.asarray(y_true)
        y_scores = np.asarray(y_scores)
        order = np.argsort(-y_scores)
        y_true = y_true[order]
        y_scores = y_scores[order]

        thresholds = np.r_[np.inf, np.unique(y_scores), -np.inf]
        P = np.sum(y_true == 1)
        N = np.sum(y_true == 0)
        tpr = []
        fpr = []
        for thresh in thresholds:
            preds = (y_scores >= thresh).astype(int)
            tp = np.sum((preds == 1) & (y_true == 1))
            fp = np.sum((preds == 1) & (y_true == 0))
            tpr.append(tp / P if P else 0.0)
            fpr.append(fp / N if N else 0.0)
        return np.array(fpr), np.array(tpr), thresholds

    def roc_auc_score(y_true, y_scores):
        fpr, tpr, _ = roc_curve(y_true, y_scores)
        # Ensure monotonicity for integration
        order = np.argsort(fpr)
        return float(np.trapz(tpr[order], fpr[order]))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not HAS_MPL:
    logger.info("matplotlib not available; plotting utilities will be skipped.")
if HAS_MPL and not HAS_SEABORN:
    logger.info("Seaborn not available; using basic matplotlib visuals for plots.")


class ModelEvaluator:
    """Evaluate anomaly detection model performance"""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive evaluation metrics

        Args:
            y_true: True labels
            y_pred: Predicted labels

        Returns:
            Dictionary of metrics

        Example:
            >>> metrics = ModelEvaluator.calculate_metrics(y_true, y_pred)
            >>> print(f"Accuracy: {metrics['accuracy']:.2f}")
        """
        # Convert predictions to binary format if needed (1/-1 to 1/0)
        y_pred_binary = np.where(y_pred == -1, 1, y_pred)
        y_pred_binary = np.where(y_pred_binary == 1, 1, 0)

        y_true_binary = np.where(y_true == -1, 1, y_true)
        y_true_binary = np.where(y_true_binary == 1, 1, 0)

        metrics = {
            'accuracy': accuracy_score(y_true_binary, y_pred_binary),
            'precision': precision_score(y_true_binary, y_pred_binary, zero_division=0),
            'recall': recall_score(y_true_binary, y_pred_binary, zero_division=0),
            'f1_score': f1_score(y_true_binary, y_pred_binary, zero_division=0),
        }

        # Calculate true/false positives/negatives
        tn, fp, fn, tp = confusion_matrix(y_true_binary, y_pred_binary).ravel()
        metrics.update({
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn),
            'detection_rate': tp / (tp + fn) if (tp + fn) > 0 else 0,
            'false_positive_rate': fp / (fp + tn) if (fp + tn) > 0 else 0,
        })

        logger.info(f"Metrics - Accuracy: {metrics['accuracy']:.3f}, "
                   f"Precision: {metrics['precision']:.3f}, "
                   f"Recall: {metrics['recall']:.3f}, "
                   f"F1: {metrics['f1_score']:.3f}")

        return metrics

    @staticmethod
    def print_classification_report(y_true: np.ndarray, y_pred: np.ndarray):
        """
        Print detailed classification report

        Args:
            y_true: True labels
            y_pred: Predicted labels
        """
        # Convert to binary
        y_pred_binary = np.where(y_pred == -1, 1, y_pred)
        y_true_binary = np.where(y_true == -1, 1, y_true)

        report = classification_report(
            y_true_binary,
            y_pred_binary,
            target_names=['Normal', 'Anomaly'],
            zero_division=0
        )

        print("\n" + "="*50)
        print("CLASSIFICATION REPORT")
        print("="*50)
        print(report)
        print("="*50 + "\n")

    @staticmethod
    def plot_confusion_matrix(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        save_path: Optional[str] = None
    ):
        """
        Plot confusion matrix

        Args:
            y_true: True labels
            y_pred: Predicted labels
            save_path: Path to save plot (optional)
        """
        # Convert to binary
        y_pred_binary = np.where(y_pred == -1, 1, y_pred)
        y_true_binary = np.where(y_true == -1, 1, y_true)

        cm = confusion_matrix(y_true_binary, y_pred_binary)

        if not HAS_MPL:
            logger.warning("matplotlib not available; skipping confusion matrix plot.")
            return

        plt.figure(figsize=(8, 6))
        if HAS_SEABORN:
            sns.heatmap(
                cm,
                annot=True,
                fmt='d',
                cmap='Blues',
                xticklabels=['Normal', 'Anomaly'],
                yticklabels=['Normal', 'Anomaly']
            )
        else:
            plt.imshow(cm, interpolation='nearest', cmap='Blues')
            plt.colorbar()
            for (i, j), value in np.ndenumerate(cm):
                plt.text(j, i, int(value), ha='center', va='center', color='black')
            plt.xticks([0, 1], ['Normal', 'Anomaly'])
            plt.yticks([0, 1], ['Normal', 'Anomaly'])

        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved confusion matrix to {save_path}")

        plt.close()

    @staticmethod
    def calculate_roc_auc(
        y_true: np.ndarray,
        y_scores: np.ndarray
    ) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Calculate ROC AUC score and curve

        Args:
            y_true: True labels
            y_scores: Prediction scores/probabilities

        Returns:
            Tuple of (auc_score, fpr, tpr)
        """
        # Convert to binary
        y_true_binary = np.where(y_true == -1, 1, y_true)

        auc = roc_auc_score(y_true_binary, y_scores)
        fpr, tpr, _ = roc_curve(y_true_binary, y_scores)

        logger.info(f"ROC AUC Score: {auc:.3f}")

        return auc, fpr, tpr

    @staticmethod
    def plot_roc_curve(
        y_true: np.ndarray,
        y_scores: np.ndarray,
        save_path: Optional[str] = None
    ):
        """
        Plot ROC curve

        Args:
            y_true: True labels
            y_scores: Prediction scores
            save_path: Path to save plot
        """
        if not HAS_MPL:
            logger.warning("matplotlib not available; skipping ROC curve plot.")
            return

        auc, fpr, tpr = ModelEvaluator.calculate_roc_auc(y_true, y_scores)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved ROC curve to {save_path}")

        plt.close()

    @staticmethod
    def evaluate_model(
        model,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        model_name: str = "Model"
    ) -> Dict[str, Any]:
        """
        Comprehensive model evaluation

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name for logging

        Returns:
            Dictionary with all evaluation results

        Example:
            >>> results = ModelEvaluator.evaluate_model(model, X_test, y_test)
        """
        logger.info(f"Evaluating {model_name}...")

        # Get predictions
        y_pred = model.predict(X_test)

        # Calculate metrics
        metrics = ModelEvaluator.calculate_metrics(y_test, y_pred)

        # Print report
        ModelEvaluator.print_classification_report(y_test, y_pred)

        # Try to get prediction scores for ROC AUC
        auc_score = None
        if hasattr(model, 'predict_proba'):
            try:
                y_scores = model.predict_proba(X_test)[:, 1]
                auc_score, _, _ = ModelEvaluator.calculate_roc_auc(y_test, y_scores)
                metrics['roc_auc'] = auc_score
            except (AttributeError, ValueError, IndexError) as e:
                logger.debug(f"Could not calculate ROC AUC with predict_proba: {e}")
        elif hasattr(model, 'score_samples'):
            try:
                y_scores = model.score_samples(X_test)
                auc_score, _, _ = ModelEvaluator.calculate_roc_auc(y_test, -y_scores)  # Negate for correct direction
                metrics['roc_auc'] = auc_score
            except (AttributeError, ValueError) as e:
                logger.debug(f"Could not calculate ROC AUC with score_samples: {e}")

        results = {
            'model_name': model_name,
            'metrics': metrics,
            'predictions': y_pred
        }

        return results

    @staticmethod
    def compare_models(
        results_list: list,
        metric: str = 'f1_score'
    ) -> pd.DataFrame:
        """
        Compare multiple models

        Args:
            results_list: List of evaluation results from evaluate_model()
            metric: Metric to sort by

        Returns:
            DataFrame with comparison results

        Example:
            >>> comparison = ModelEvaluator.compare_models([result1, result2])
        """
        comparison_data = []

        for result in results_list:
            row = {
                'Model': result['model_name'],
                **result['metrics']
            }
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)

        # Sort by specified metric
        if metric in df.columns:
            df = df.sort_values(metric, ascending=False)

        logger.info(f"\nModel Comparison (sorted by {metric}):")
        print("\n" + df.to_string(index=False))

        return df


def evaluate_model(model, X_test: pd.DataFrame, y_test: np.ndarray) -> Dict[str, Any]:
    """
    Convenience function to evaluate a model

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels

    Returns:
        Evaluation results dictionary
    """
    return ModelEvaluator.evaluate_model(model, X_test, y_test)
