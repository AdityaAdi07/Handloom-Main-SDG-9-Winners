import os
import joblib
import pandas as pd

class InferenceEngine:
    def __init__(self, registry_path=None):
        if registry_path is None:
            registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
            
        self.defect_model = joblib.load(os.path.join(registry_path, 'defect_model.joblib'))
        self.fault_model = joblib.load(os.path.join(registry_path, 'fault_model.joblib'))
        self.maintenance_model = joblib.load(os.path.join(registry_path, 'maintenance_model.joblib'))
        self.quality_model = joblib.load(os.path.join(registry_path, 'quality_model.joblib'))
        
        self.yarn_encoder = joblib.load(os.path.join(registry_path, 'yarn_encoder.joblib'))
        quality_map = joblib.load(os.path.join(registry_path, 'quality_encoder.joblib'))
        self.quality_decoder = {v: k for k, v in quality_map.items()}
        
        self.fault_decoder = {
            0: "no_fault",
            1: "thread_break",
            2: "overheat",
            3: "motor_fault"
        }

    def predict_defect(self, req):
        pattern = [item for sublist in req.pattern_matrix for item in sublist]
        features = pd.DataFrame([{
            'machine_speed': req.machine_speed,
            'thread_warp_tension': req.thread_warp_tension,
            'thread_weft_tension': req.thread_weft_tension,
            'environment_temperature': req.environment_temperature,
            'environment_humidity': req.environment_humidity,
            'environment_vibration': req.environment_vibration,
            'energy_power': req.energy_power,
            'pattern_0_0': pattern[0], 'pattern_0_1': pattern[1], 'pattern_0_2': pattern[2],
            'pattern_1_0': pattern[3], 'pattern_1_1': pattern[4], 'pattern_1_2': pattern[5],
            'pattern_2_0': pattern[6], 'pattern_2_1': pattern[7], 'pattern_2_2': pattern[8]
        }])
        return float(self.defect_model.predict(features)[0])

    def predict_fault(self, req):
        features = pd.DataFrame([{
            'machine_speed': req.machine_speed,
            'environment_vibration': req.environment_vibration,
            'thread_warp_tension': req.thread_warp_tension,
            'thread_weft_tension': req.thread_weft_tension,
            'energy_power': req.energy_power,
            'control_speed_error': req.control_speed_error
        }])
        fault_class = int(self.fault_model.predict(features)[0])
        return self.fault_decoder.get(fault_class, "unknown")

    def predict_maintenance(self, req):
        features = pd.DataFrame([{
            'fault_anomaly_score': req.fault_anomaly_score,  
            'environment_vibration': req.environment_vibration,
            'energy_power': req.energy_power,
            'machine_cycles': req.machine_cycles,
            'fault_thread_break': req.fault_thread_break,
            'fault_motor_fault': req.fault_motor_fault,
            'fault_overheat': req.fault_overheat
        }])
        return bool(self.maintenance_model.predict(features)[0])

    def predict_quality(self, req):
        pattern = [item for sublist in req.pattern_matrix for item in sublist]
        features = pd.DataFrame([{
            'thread_warp_tension': req.thread_warp_tension,
            'thread_weft_tension': req.thread_weft_tension,
            'machine_speed': req.machine_speed,
            'environment_humidity': req.environment_humidity,
            'production_defect_rate': req.production_defect_rate, 
            'pattern_0_0': pattern[0], 'pattern_0_1': pattern[1], 'pattern_0_2': pattern[2],
            'pattern_1_0': pattern[3], 'pattern_1_1': pattern[4], 'pattern_1_2': pattern[5],
            'pattern_2_0': pattern[6], 'pattern_2_1': pattern[7], 'pattern_2_2': pattern[8]
        }])
        quality_class = int(self.quality_model.predict(features)[0])
        return self.quality_decoder.get(quality_class, "Unknown")
