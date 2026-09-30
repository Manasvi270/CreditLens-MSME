import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, 
    average_precision_score, 
    brier_score_loss, 
    confusion_matrix, 
    precision_recall_fscore_support
)
from sklearn.calibration import calibration_curve

def evaluate_risk_model(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """
    Computes comprehensive evaluation metrics for a credit risk model:
    - ROC-AUC & PR-AUC
    - Brier Score (calibration goodness-of-fit)
    - Precision, Recall, F1 Score
    - Confusion Matrix (TN, FP, FN, TP)
    - Calibration Curve Coordinates
    """
    y_pred = (y_prob >= threshold).astype(int)
    
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    brier = float(brier_score_loss(y_true, y_prob))
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy='uniform')
    
    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "calibration_curve": {
            "prob_true": [round(x, 4) for x in prob_true.tolist()],
            "prob_pred": [round(x, 4) for x in prob_pred.tolist()]
        }
    }
