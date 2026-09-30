import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from ml.config import (
    MSME_DATA_PATH, CASHFLOW_DATA_PATH, PRIMARY_MODEL_PATH,
    PREPROCESSOR_PATH, RANDOM_SEED, CATEGORICAL_FEATURES, NUMERICAL_FEATURES
)
from ml.preprocess import load_and_prepare_dataset
from ml.evaluate import evaluate_risk_model

def get_detailed_test_metrics():
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    X = df[feature_cols]
    y = df['default_label']
    
    # 80/20 Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(PRIMARY_MODEL_PATH)
    
    X_test_proc = preprocessor.transform(X_test)
    y_test_prob = model.predict_proba(X_test_proc)[:, 1]
    y_test_pred = (y_test_prob >= 0.5).astype(int)
    
    acc = accuracy_score(y_test, y_test_pred)
    eval_dict = evaluate_risk_model(y_test.values, y_test_prob, threshold=0.5)
    
    print("=== HELD-OUT TEST SET EVALUATION REPORT ===")
    print(f"Total Dataset Size: {len(df)} MSMEs")
    print(f"Training Samples: {len(X_train)} ({len(X_train)/len(df):.1%})")
    print(f"Testing Samples: {len(X_test)} ({len(X_test)/len(df):.1%})")
    print(f"Test Set Default Cases (Positive Class = 1): {int(y_test.sum())} ({y_test.mean():.2%})")
    print(f"Test Set Non-Default Cases (Negative Class = 0): {int((y_test == 0).sum())} ({(y_test == 0).mean():.2%})")
    
    print("\n--- METRICS BREAKDOWN ---")
    print(f"1. Accuracy: {acc:.4f} ({acc:.2%})")
    print(f"2. ROC-AUC: {eval_dict['roc_auc']:.4f}")
    print(f"3. PR-AUC: {eval_dict['pr_auc']:.4f}")
    print(f"4. Precision: {eval_dict['precision']:.4f}")
    print(f"5. Recall: {eval_dict['recall']:.4f}")
    print(f"6. F1-Score: {eval_dict['f1_score']:.4f}")
    print(f"7. Brier Score: {eval_dict['brier_score']:.4f}")
    
    cm = eval_dict['confusion_matrix']
    print("\n--- CONFUSION MATRIX ---")
    print(f"True Negatives (TN):  {cm['true_negatives']}")
    print(f"False Positives (FP): {cm['false_positives']}")
    print(f"False Negatives (FN): {cm['false_negatives']}")
    print(f"True Positives (TP):  {cm['true_positives']}")
    
    cal = eval_dict['calibration_curve']
    print("\n--- CALIBRATION RESULTS (Predicted vs Observed Default Rate) ---")
    for pred, obs in zip(cal['prob_pred'], cal['prob_true']):
        print(f"  Predicted Probability: {pred:.2%}  |  Observed Actual Defaults: {obs:.2%}")

if __name__ == "__main__":
    get_detailed_test_metrics()
