from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.base import clone


from sklearn.metrics import (
    confusion_matrix, ConfusionMatrixDisplay,
    roc_curve, roc_auc_score,
    classification_report, mean_squared_error,
    precision_recall_fscore_support
)

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold

from imblearn.pipeline import Pipeline 
from imblearn.over_sampling import SMOTE
from collections import OrderedDict

import warnings
warnings.filterwarnings("ignore")

class ResultCollector:
    def __init__(self):
        self.results = OrderedDict() 
        
    def add_model(self, name, train_rmse, test_rmse, expected_loss):
        """Add or update a model's results."""
        self.results[name] = {
            'Train RMSE': train_rmse,
            'Test RMSE': test_rmse,
            'Expected Loss' : expected_loss, 
        }
        return self.get_table()
    
    def get_table(self, style=True):
        """Get the results table with optional styling."""
        df = pd.DataFrame(self.results).T
        if style:
            return df.style.format("{:.3f}").background_gradient(cmap='RdYlGn_r', axis=None)
        return df


def random_split(df, label_col="relevance_text"):
    X = df.drop(columns=[label_col])
    y = df[label_col]
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Diagnostics helper function
def diagnostics(y_train, y_train_probs, y_valid, y_valid_probs, model_name="Model"):
    
    # 1️⃣ Find best threshold based on F1
    thresholds = np.linspace(0.01, 0.99, 100)
    f1_scores = []

    for t in thresholds:
        y_pred = (y_valid_probs >= t).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(y_valid, y_pred, average="binary")
        f1_scores.append(f1)

    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx]

    # 2️⃣ Confusion Matrix
    y_pred = (y_valid_probs >= best_threshold).astype(int)
    cm = confusion_matrix(y_valid, y_pred, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    disp.plot(cmap="Blues", values_format=".2%")
    plt.title(f"{model_name} - Confusion Matrix (Threshold = {best_threshold:.2f})")
    plt.grid(False)
    plt.tight_layout()
    plt.show()

    # 3️⃣ ROC Curve
    fpr, tpr, _ = roc_curve(y_valid, y_valid_probs)
    auc_score = roc_auc_score(y_valid, y_valid_probs)

    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, label=f"ROC AUC = {auc_score:.2f}")
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"{model_name} - ROC Curve")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 4️⃣ Calibration Curve
    prob_true, prob_pred = calibration_curve(y_valid, y_valid_probs, n_bins=10, strategy='quantile')
    plt.figure(figsize=(7, 5))
    plt.plot(prob_pred, prob_true, marker='o', label='Model')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfect Calibration')
    plt.title(f"{model_name} - Calibration Curve")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 6️⃣ Histogram by Class
    plt.figure(figsize=(9, 5))
    sns.histplot(x=y_valid_probs, hue=y_valid, bins=30, kde=True, stat='density', common_norm=False)
    plt.axvline(best_threshold, color='red', linestyle='--', label=f'Threshold = {best_threshold:.2f}')
    plt.title(f"{model_name} - Predicted Probability Distribution by Class")
    plt.xlabel("Predicted Probability for Class 1")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 7️⃣ Classification Report
    print(f"\n📊 Classification Report (Threshold = {best_threshold:.2f}):")
    print(classification_report(y_valid, y_pred, digits=3))

    # 8️⃣ RMSE on train and test
    rmse_train = np.sqrt(mean_squared_error(y_train, y_train_probs))
    rmse_valid = np.sqrt(mean_squared_error(y_valid, y_valid_probs))
    print(f"\n📈 Train RMSE: {rmse_train:.4f}")
    print(f"📈 Test  RMSE: {rmse_valid:.4f}")

    return {
    "Model": model_name,
    "Threshold": best_threshold,
    "Train RMSE": rmse_train,
    "Test RMSE": rmse_valid,
    "AUC": auc_score,
    "F1": f1_scores[best_idx]
}


# # Function to calculate TP % and FP % from predictions
# def calculate_tp_fp_percent(y_true, y_pred):
#     cm = confusion_matrix(y_true, y_pred)
#     tn, fp, fn, tp = cm.ravel()
#     tp_percent = tp / (tp + fn) if (tp + fn) > 0 else 0
#     fp_percent = fp / (fp + tn) if (fp + tn) > 0 else 0
#     return tp_percent, fp_percent

# Confusion matrix helper function


def compute_expected_loss(y_true, y_probs, thresholds=np.linspace(0.01, 0.99, 100),
                          fp_cost=1, fn_cost=4):
    losses = []
    for t in thresholds:
        y_pred = (y_probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        total = tn + fp + fn + tp
        loss = (fp_cost * fp + fn_cost * fn) / total
        losses.append(loss)
    best_idx = np.argmin(losses)
    return thresholds[best_idx], losses[best_idx]


def matrix(y_train, train_probs, y_valid, y_valid_probs, model_name="Model"):
    # # 1️⃣ Find best threshold based on F1
    # from sklearn.metrics import precision_recall_fscore_support

    # thresholds = np.linspace(0.01, 0.99, 100)
    # f1_scores = []

    # for t in thresholds:
    #     y_pred = (y_valid_probs >= t).astype(int)
    #     _, _, f1, _ = precision_recall_fscore_support(y_valid, y_pred, average="binary")
    #     f1_scores.append(f1)

    # best_idx = np.argmax(f1_scores)
    # best_threshold = thresholds[best_idx]
    best_threshold, expected_loss = compute_expected_loss(y_valid, y_valid_probs)

    # 2️⃣ Confusion Matrix
    y_pred = (y_valid_probs >= best_threshold).astype(int)
    cm = confusion_matrix(y_valid, y_pred, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    disp.plot(cmap="Blues", values_format=".2%")
    plt.title(f"Confusion Matrix @ Cost-Optimized Threshold = {best_threshold:.2f}")
    plt.grid(False)
    plt.tight_layout()
    plt.show()
    return best_threshold




def run_model_with_gridsearch(name, pipe, param_grid, X_train_full, y_train, X_valid_full, y_valid,
                              results, best_models, diagnostics_fn, collector=None,
                              feature_list=None, categorical_features=None):
    print(f"🔍 Running model: {name}")

    # Subset features
    if feature_list is not None:
        X_train = X_train_full[feature_list]
        X_valid = X_valid_full[feature_list]
    else:
        X_train = X_train_full.copy()
        X_valid = X_valid_full.copy()

    # Build preprocessor
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), [f for f in feature_list if f not in categorical_features]),
        ('cat', OneHotEncoder(handle_unknown='ignore'), [f for f in feature_list if f in categorical_features])
    ])

    # Inject preprocessor into pipeline dynamically if not already there
    if not any(step[0] == 'preprocessor' for step in pipe.steps):
        pipe.steps.insert(0, ('preprocessor', preprocessor))
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cloned_pipe = clone(pipe)
    grid = GridSearchCV(cloned_pipe, param_grid, cv=cv, scoring='roc_auc', n_jobs=-1, verbose=0)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    best_models[name] = best_model

    train_probs = best_model.predict_proba(X_train)[:, 1]
    valid_probs = best_model.predict_proba(X_valid)[:, 1]

    output = diagnostics_fn(y_train, train_probs, y_valid, valid_probs, model_name=name)
    results.append(output)


        # --- Business Loss Summary (Only Print, Do Not Log) ---
    threshold, expected_loss = compute_expected_loss(y_valid, valid_probs)
    print(f"\n📉 Business Cost Evaluation for {name}:")
    print(f"🔹 Best Threshold (Cost-Optimized): {threshold:.3f}")
    print(f"🔹 Expected Loss: {expected_loss:.3f}  [FN cost = 4, FP cost = 1]\n")
    
    if collector is not None:
        train_rmse = np.sqrt(mean_squared_error(y_train, train_probs))
        test_rmse = np.sqrt(mean_squared_error(y_valid, valid_probs))
        expected_loss = expected_loss
        collector.add_model(name, train_rmse, test_rmse, expected_loss)
        print(f"📊 {name}: Train RMSE = {train_rmse:.4f}, Valid RMSE = {test_rmse:.4f}")
    
    print(f"✅ Finished: {name}\n")
    return best_model

