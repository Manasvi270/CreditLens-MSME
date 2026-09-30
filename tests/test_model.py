import os
import json
import pytest
import joblib
import pandas as pd
from ml.config import (
    PRIMARY_MODEL_PATH, PREPROCESSOR_PATH, CHALLENGER_MODEL_PATH,
    METRICS_REPORT_PATH, MSME_DATA_PATH, CASHFLOW_DATA_PATH,
    CATEGORICAL_FEATURES, NUMERICAL_FEATURES
)
from ml.preprocess import load_and_prepare_dataset
from ml.train_model import train_and_save_models

def test_model_training_and_artifact_generation():
    """Verify model training executes and saves all required artifacts."""
    metrics = train_and_save_models()
    
    assert os.path.exists(PRIMARY_MODEL_PATH), "Primary model artifact missing."
    assert os.path.exists(PREPROCESSOR_PATH), "Preprocessor artifact missing."
    assert os.path.exists(CHALLENGER_MODEL_PATH), "Challenger model artifact missing."
    assert os.path.exists(METRICS_REPORT_PATH), "Metrics report missing."
    
    assert "primary_model_calibrated" in metrics
    assert "roc_auc" in metrics["primary_model_calibrated"]
    assert metrics["primary_model_calibrated"]["roc_auc"] > 0.65, "Model ROC-AUC is too low."

def test_artifacts_loadable():
    """Verify saved joblib artifacts load cleanly."""
    model = joblib.load(PRIMARY_MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    challenger = joblib.load(CHALLENGER_MODEL_PATH)
    
    assert model is not None
    assert preprocessor is not None
    assert challenger is not None

def test_no_target_leakage():
    """Verify target column and identifier are not included in training feature set."""
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    
    assert 'default_label' not in feature_cols, "Target leakage: default_label in features."
    assert 'msme_id' not in feature_cols, "Target leakage: msme_id in features."
    
    for col in feature_cols:
        assert col in df.columns, f"Feature {col} missing from prepared dataframe."

def test_evaluation_report_content():
    """Verify evaluation JSON report contains required metrics."""
    with open(METRICS_REPORT_PATH, 'r') as f:
        report = json.load(f)
        
    for key in ["primary_model_calibrated", "primary_model_uncalibrated", "challenger_model_xgb"]:
        assert key in report
        assert "roc_auc" in report[key]
        assert "pr_auc" in report[key]
        assert "brier_score" in report[key]
        assert "confusion_matrix" in report[key]
