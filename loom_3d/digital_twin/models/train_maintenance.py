import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, roc_auc_score

def train_maintenance_model(data_path=None, registry_path=None):
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
    if registry_path is None:
        registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
        
    print("--- Training Model 3: Maintenance Prediction (Classification) ---")
    
    # Load processed data
    df = pd.read_csv(data_path)
    
    # Define features and target
    features = [
        'fault_anomaly_score', 'environment_vibration', 'energy_power',
        'machine_cycles', 'fault_thread_break', 'fault_motor_fault', 'fault_overheat'
    ]
    target = 'maintenance_required'
    
    X = df[features]
    y = df[target]
    
    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Initialize and train model handling heavy class imbalance
    print("Training Random Forest Classifier (with class balancing)...")
    # Due to extreme imbalance (~0.3%), 'balanced_subsample' or 'balanced' is critical
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced_subsample', max_depth=8, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if len(model.classes_) > 1 else y_pred
    
    f1 = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob) if len(model.classes_) > 1 else 0.0
    
    print(f"Metrics - F1 Score: {f1:.4f}, ROC-AUC: {roc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Save the model
    os.makedirs(registry_path, exist_ok=True)
    model_path = os.path.join(registry_path, 'maintenance_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}\n")

if __name__ == "__main__":
    train_maintenance_model()
