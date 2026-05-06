import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score

def train_defect_model(data_path=None, registry_path=None):
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.csv')
    if registry_path is None:
        registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
        
    print("--- Training Model 1: Defect Rate (Regression) ---")
    
    # Load processed data
    df = pd.read_csv(data_path)
    
    # Define features and target
    features = [
        'machine_speed', 'thread_warp_tension', 'thread_weft_tension',
        'environment_temperature', 'environment_humidity', 'environment_vibration',
        'energy_power',
        'pattern_0_0', 'pattern_0_1', 'pattern_0_2',
        'pattern_1_0', 'pattern_1_1', 'pattern_1_2',
        'pattern_2_0', 'pattern_2_1', 'pattern_2_2'
    ]
    target = 'production_defect_rate'
    
    X = df[features]
    y = df[target]
    
    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train model
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Metrics - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
    
    # Save the model
    os.makedirs(registry_path, exist_ok=True)
    model_path = os.path.join(registry_path, 'defect_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}\n")

if __name__ == "__main__":
    train_defect_model()
