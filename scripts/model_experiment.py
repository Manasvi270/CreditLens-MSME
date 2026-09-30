import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, precision_recall_fscore_support, accuracy_score, balanced_accuracy_score
)
from sklearn.calibration import calibration_curve
from xgboost import XGBClassifier

from ml.config import (
    MSME_DATA_PATH, CASHFLOW_DATA_PATH, RANDOM_SEED,
    CATEGORICAL_FEATURES, NUMERICAL_FEATURES
)
from ml.preprocess import load_and_prepare_dataset, build_preprocessing_pipeline

def run_experiment():
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    X = df[feature_cols]
    y = df['default_label']
    
    # Same 80/20 Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    
    preprocessor = build_preprocessing_pipeline()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    
    print("=== CONTROLLED RISK MODEL EXPERIMENT ===")
    print(f"Train Set: {len(X_train)} samples | Test Set: {len(X_test)} samples\n")
    
    # -------------------------------------------------------------
    # Model 1: Baseline Calibrated Logistic Regression (Unweighted)
    # -------------------------------------------------------------
    base_lr = LogisticRegression(C=1.0, solver='liblinear', random_state=RANDOM_SEED)
    cal_lr_baseline = CalibratedClassifierCV(estimator=base_lr, method='sigmoid', cv=5)
    cal_lr_baseline.fit(X_train_proc, y_train)
    prob_test_baseline = cal_lr_baseline.predict_proba(X_test_proc)[:, 1]
    
    # -------------------------------------------------------------
    # Model 2: Calibrated Logistic Regression (Balanced Class Weight)
    # -------------------------------------------------------------
    base_lr_balanced = LogisticRegression(C=1.0, solver='liblinear', class_weight='balanced', random_state=RANDOM_SEED)
    cal_lr_balanced = CalibratedClassifierCV(estimator=base_lr_balanced, method='sigmoid', cv=5)
    cal_lr_balanced.fit(X_train_proc, y_train)
    prob_test_balanced = cal_lr_balanced.predict_proba(X_test_proc)[:, 1]
    
    # -------------------------------------------------------------
    # Model 3: Calibrated XGBoost Challenger
    # -------------------------------------------------------------
    base_xgb = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, random_state=RANDOM_SEED, eval_metric='logloss')
    cal_xgb = CalibratedClassifierCV(estimator=base_xgb, method='sigmoid', cv=5)
    cal_xgb.fit(X_train_proc, y_train)
    prob_test_xgb = cal_xgb.predict_proba(X_test_proc)[:, 1]

    def eval_model_at_thresh(y_true, probas, thresh):
        preds = (probas >= thresh).astype(int)
        acc = accuracy_score(y_true, preds)
        bal_acc = balanced_accuracy_score(y_true, preds)
        roc = roc_auc_score(y_true, probas)
        pr = average_precision_score(y_true, probas)
        brier = brier_score_loss(y_true, probas)
        
        tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        approval_rate = (tn + fn) / len(y_true)
        
        return {
            "thresh": thresh,
            "acc": acc,
            "bal_acc": bal_acc,
            "roc": roc,
            "pr": pr,
            "prec": prec,
            "rec": rec,
            "spec": spec,
            "f1": f1,
            "brier": brier,
            "approval_rate": approval_rate,
            "cm": (tn, fp, fn, tp)
        }

    # -------------------------------------------------------------
    # EXPERIMENT PART 1: Threshold Sweeps (0.10 to 0.70) on Baseline LR
    # -------------------------------------------------------------
    print("--- THRESHOLD SWEEP (Baseline Calibrated LR) ---")
    thresholds = [0.10, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70]
    thresh_results = []
    for t in thresholds:
        res = eval_model_at_thresh(y_test.values, prob_test_baseline, t)
        thresh_results.append(res)
        tn, fp, fn, tp = res['cm']
        print(f"Thresh {t:.2f} | Acc: {res['acc']:.2%} | Prec: {res['prec']:.2%} | Rec: {res['rec']:.2%} | Spec: {res['spec']:.2%} | F1: {res['f1']:.4f} | AppRate: {res['approval_rate']:.2%} | CM [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
        
    # -------------------------------------------------------------
    # EXPERIMENT PART 2: Candidate Model Comparison Table
    # -------------------------------------------------------------
    print("\n=== CANDIDATE COMPARISON AT SELECTED THRESHOLDS ===")
    candidates = [
        ("Baseline Calibrated LR", prob_test_baseline, 0.50),
        ("Baseline Calibrated LR", prob_test_baseline, 0.20),
        ("Baseline Calibrated LR", prob_test_baseline, 0.18),
        ("Balanced Calibrated LR", prob_test_balanced, 0.50),
        ("Balanced Calibrated LR", prob_test_balanced, 0.20),
        ("Calibrated XGBoost", prob_test_xgb, 0.50),
        ("Calibrated XGBoost", prob_test_xgb, 0.20),
    ]
    
    comp_table = []
    for name, probas, t in candidates:
        r = eval_model_at_thresh(y_test.values, probas, t)
        comp_table.append({
            "Model": name,
            "Threshold": f"{t:.2f}",
            "ROC-AUC": f"{r['roc']:.4f}",
            "PR-AUC": f"{r['pr']:.4f}",
            "Precision": f"{r['prec']:.2%}",
            "Recall": f"{r['rec']:.2%}",
            "F1": f"{r['f1']:.4f}",
            "Specificity": f"{r['spec']:.2%}",
            "Brier": f"{r['brier']:.4f}",
            "Bal Acc": f"{r['bal_acc']:.2%}",
            "TN": r['cm'][0],
            "FP": r['cm'][1],
            "FN": r['cm'][2],
            "TP": r['cm'][3]
        })
        
    df_comp = pd.DataFrame(comp_table)
    print(df_comp.to_string(index=False))

    # -------------------------------------------------------------
    # EXPERIMENT PART 3: Calibration Curve Analysis
    # -------------------------------------------------------------
    print("\n=== CALIBRATION CURVE COMPARISON ===")
    models_to_cal = [
        ("Baseline Calibrated LR", prob_test_baseline),
        ("Balanced Calibrated LR", prob_test_balanced),
        ("Calibrated XGBoost", prob_test_xgb)
    ]
    for mname, probas in models_to_cal:
        prob_true, prob_pred = calibration_curve(y_test.values, probas, n_bins=5, strategy='uniform')
        print(f"\n{mname}:")
        for pt, pp in zip(prob_pred, prob_true):
            print(f"  Predicted PD: {pt:.2%} -> Actual Default Rate: {pp:.2%}")

if __name__ == "__main__":
    run_experiment()
