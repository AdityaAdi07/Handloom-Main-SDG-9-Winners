import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score

def train_fault_model(data_path=None, registry_path=None):
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
    if registry_path is None:
        registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
        
    print("--- Training Model 2: Fault Prediction (Classification) ---")
    
    # Load processed data
    df = pd.read_csv(data_path)
    
    # Define features and target
    features = [
        'machine_speed', 'environment_vibration', 'thread_warp_tension',
        'thread_weft_tension', 'energy_power', 'control_speed_error'
    ]
    target = 'fault_class'
    
    X = df[features]
    y = df[target]
    
    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Initialize and train model handling class imbalance
    print("Training Random Forest Classifier (with class balancing)...")
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='macro')
    
    print(f"Metrics - F1 Score (Macro): {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Save the model
    os.makedirs(registry_path, exist_ok=True)
    model_path = os.path.join(registry_path, 'fault_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}\n")

if __name__ == "__main__":
    train_fault_model()
