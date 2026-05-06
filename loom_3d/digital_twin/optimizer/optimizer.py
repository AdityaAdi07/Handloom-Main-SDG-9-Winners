import numpy as np
import pandas as pd
import joblib
import os

class OptimizerEngine:
    def __init__(self, registry_path=None):
        if registry_path is None:
            registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
            
        model_path = os.path.join(registry_path, 'defect_model.joblib')
        self.defect_model = joblib.load(model_path)
        
        # Load yarn encoder to translate string back to int if needed
        self.yarn_encoder = joblib.load(os.path.join(registry_path, 'yarn_encoder.joblib'))
        
        # Grid definition
        self.speeds = np.arange(80, 155, 5)
        self.warp_tensions = np.arange(4.0, 8.5, 0.5)
        self.weft_tensions = np.arange(4.0, 8.5, 0.5)

    def optimize(self, env_data):
        """
        Runs a simulation grid search to find the optimal machine settings
        for the lowest predicted defect rate given fixed environment/pattern.
        """
        best_defect_rate = float('inf')
        best_settings = {}
        
        # Prepare the base features that do not change
        yarn_type_encoded = self.yarn_encoder.get(env_data.get('yarn_type', 'silk'), 0)
        
        # Flatten pattern_matrix safely
        pattern = env_data.get('pattern_matrix', [[1,0,1], [0,1,0], [1,1,0]])
        pattern_flat = [item for sublist in pattern for item in sublist]
        
        base_features = {
            'environment_temperature': env_data.get('temperature', 32.0),
            'environment_humidity': env_data.get('humidity', 65.0),
            'environment_vibration': env_data.get('vibration', 0.05),
            'energy_power': env_data.get('energy_power', 800), # Not provided in query, assume typical
            'pattern_0_0': pattern_flat[0], 'pattern_0_1': pattern_flat[1], 'pattern_0_2': pattern_flat[2],
            'pattern_1_0': pattern_flat[3], 'pattern_1_1': pattern_flat[4], 'pattern_1_2': pattern_flat[5],
            'pattern_2_0': pattern_flat[6], 'pattern_2_1': pattern_flat[7], 'pattern_2_2': pattern_flat[8]
        }

        # Build grid of combinations
        grid_rows = []
        for s in self.speeds:
            for wa in self.warp_tensions:
                for we in self.weft_tensions:
                    row = base_features.copy()
                    row['machine_speed'] = s
                    row['thread_warp_tension'] = wa
                    row['thread_weft_tension'] = we
                    grid_rows.append(row)
                    
        df_grid = pd.DataFrame(grid_rows)
        
        # Reorder columns to exactly match Model 1 training order
        feature_order = [
            'machine_speed', 'thread_warp_tension', 'thread_weft_tension',
            'environment_temperature', 'environment_humidity', 'environment_vibration',
            'energy_power',
            'pattern_0_0', 'pattern_0_1', 'pattern_0_2',
            'pattern_1_0', 'pattern_1_1', 'pattern_1_2',
            'pattern_2_0', 'pattern_2_1', 'pattern_2_2'
        ]
        df_grid = df_grid[feature_order]
        
        # Predict defect rate for all combinations
        predictions = self.defect_model.predict(df_grid)
        
        # Find the best combination
        best_idx = np.argmin(predictions)
        best_defect_rate = predictions[best_idx]
        
        best_settings = {
            "best_speed": float(df_grid.iloc[best_idx]['machine_speed']),
            "best_warp_tension": float(df_grid.iloc[best_idx]['thread_warp_tension']),
            "best_weft_tension": float(df_grid.iloc[best_idx]['thread_weft_tension']),
            "expected_defect_rate": float(best_defect_rate),
            "optimization_status": "ok"
        }
        
        # Add alert logic if the best defect rate is still high
        if best_defect_rate > 0.75:
            # Extract feature importances
            importances = self.defect_model.feature_importances_
            feature_imp_df = pd.DataFrame({'feature': feature_order, 'importance': importances})
            top_features = feature_imp_df.sort_values(by='importance', ascending=False).head(3)['feature'].tolist()
            
            best_settings["alert"] = "Warning: Even optimal settings predict high defect rate."
            best_settings["driving_factors"] = top_features
            best_settings["recommendation"] = "Reduce speed, adjust tension, or check vibration."
            
        return best_settings
