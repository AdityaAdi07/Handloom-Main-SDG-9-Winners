import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score

def train_quality_model(data_path=None, registry_path=None):
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
    if registry_path is None:
        registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
        
    print("--- Training Model 4: Fabric Quality (Classification) ---")
    
    # Load processed data
    df = pd.read_csv(data_path)
    
    # Define features and target
    features = [
        'thread_warp_tension', 'thread_weft_tension', 'machine_speed',
        'environment_humidity', 'production_defect_rate',
        'pattern_0_0', 'pattern_0_1', 'pattern_0_2',
        'pattern_1_0', 'pattern_1_1', 'pattern_1_2',
        'pattern_2_0', 'pattern_2_1', 'pattern_2_2'
    ]
    target = 'production_quality'
    
    X = df[features]
    y = df[target]
    
    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train model
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='weighted')
    acc = accuracy_score(y_test, y_pred)
    
    print(f"Metrics - Accuracy: {acc:.4f}, F1 Score (Weighted): {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Save the model
    os.makedirs(registry_path, exist_ok=True)
    model_path = os.path.join(registry_path, 'quality_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}\n")

if __name__ == "__main__":
    train_quality_model()
