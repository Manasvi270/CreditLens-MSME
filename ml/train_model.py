import os
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier

from ml.config import (
    MSME_DATA_PATH, CASHFLOW_DATA_PATH, MODEL_DIR,
    PRIMARY_MODEL_PATH, PREPROCESSOR_PATH, CHALLENGER_MODEL_PATH,
    METRICS_REPORT_PATH, RANDOM_SEED, CATEGORICAL_FEATURES, NUMERICAL_FEATURES
)
from ml.preprocess import load_and_prepare_dataset, build_preprocessing_pipeline
from ml.evaluate import evaluate_risk_model

def train_and_save_models():
    """
    Trains the Primary Calibrated Logistic Scorecard model and XGBoost Challenger model.
    Saves preprocessor, models, and evaluation metrics report.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Load dataset
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    X = df[feature_cols]
    y = df['default_label']
    
    # 2. Stratified Train/Test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    
    print(f"Dataset split: Training={len(X_train)} rows, Testing={len(X_test)} rows")
    print(f"Train Default Rate: {y_train.mean():.2%}, Test Default Rate: {y_test.mean():.2%}")
    
    # 3. Fit preprocessing pipeline
    preprocessor = build_preprocessing_pipeline()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    
    # 4. Train Primary Model (Logistic Regression + Platt Sigmoid Calibration)
    base_lr = LogisticRegression(C=1.0, solver='liblinear', random_state=RANDOM_SEED)
    calibrated_lr = CalibratedClassifierCV(estimator=base_lr, method='sigmoid', cv=5)
    calibrated_lr.fit(X_train_proc, y_train)
    
    # Evaluate Primary Model
    y_test_prob_primary = calibrated_lr.predict_proba(X_test_proc)[:, 1]
    primary_metrics = evaluate_risk_model(y_test.values, y_test_prob_primary)
    
    # Uncalibrated baseline LR metrics for comparison
    base_lr.fit(X_train_proc, y_train)
    y_test_prob_uncalibrated = base_lr.predict_proba(X_test_proc)[:, 1]
    uncalibrated_metrics = evaluate_risk_model(y_test.values, y_test_prob_uncalibrated)
    
    # 5. Train Challenger Model (XGBoost)
    xgb_model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.08,
        random_state=RANDOM_SEED,
        eval_metric='logloss'
    )
    xgb_model.fit(X_train_proc, y_train)
    y_test_prob_challenger = xgb_model.predict_proba(X_test_proc)[:, 1]
    challenger_metrics = evaluate_risk_model(y_test.values, y_test_prob_challenger)
    
    # 6. Save model artifacts
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    joblib.dump(calibrated_lr, PRIMARY_MODEL_PATH)
    joblib.dump(xgb_model, CHALLENGER_MODEL_PATH)
    
    metrics_report = {
        "primary_model_calibrated": primary_metrics,
        "primary_model_uncalibrated": uncalibrated_metrics,
        "challenger_model_xgb": challenger_metrics
    }
    
    with open(METRICS_REPORT_PATH, 'w') as f:
        json.dump(metrics_report, f, indent=2)
        
    print("[OK] Trained models and saved artifacts successfully.")
    print(f"  Primary Calibrated LR ROC-AUC: {primary_metrics['roc_auc']:.4f} | PR-AUC: {primary_metrics['pr_auc']:.4f} | Brier: {primary_metrics['brier_score']:.4f}")
    print(f"  Primary Uncalibrated LR ROC-AUC: {uncalibrated_metrics['roc_auc']:.4f} | Brier: {uncalibrated_metrics['brier_score']:.4f}")
    print(f"  Challenger XGBoost ROC-AUC:    {challenger_metrics['roc_auc']:.4f} | PR-AUC: {challenger_metrics['pr_auc']:.4f} | Brier: {challenger_metrics['brier_score']:.4f}")
    
    return metrics_report

if __name__ == "__main__":
    train_and_save_models()
