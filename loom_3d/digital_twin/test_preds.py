import pandas as pd
import json

df = pd.read_csv('data/processed_data.csv')

def get_row_as_dict(df_subset, features):
    row = df_subset.iloc[0]
    return {f: float(row[f]) if '.' in str(row[f]) or type(row[f]) == float else int(row[f]) for f in features}

print("====== MAINTENANCE ======")
m_features = ['fault_anomaly_score', 'environment_vibration', 'energy_power', 'machine_cycles', 'fault_thread_break', 'fault_motor_fault', 'fault_overheat']
print("Maintenance FALSE (Case 1):")
print(json.dumps(get_row_as_dict(df[df['maintenance_required'] == 0], m_features), indent=2))
print("Maintenance TRUE (Case 2 - Motor Fault):")
print(json.dumps(get_row_as_dict(df[(df['maintenance_required'] == 1) & (df['fault_motor_fault'] == 1)], m_features), indent=2))
print("Maintenance TRUE (Case 3 - High Anomaly):")
print(json.dumps(get_row_as_dict(df[(df['maintenance_required'] == 1) & (df['fault_anomaly_score'] > 0.8)], m_features), indent=2))

print("====== QUALITY ======")
q_features = ['thread_warp_tension', 'thread_weft_tension', 'machine_speed', 'environment_humidity', 'production_defect_rate', 'pattern_0_0', 'pattern_0_1', 'pattern_0_2', 'pattern_1_0', 'pattern_1_1', 'pattern_1_2', 'pattern_2_0', 'pattern_2_1', 'pattern_2_2']

def format_quality(row_dict):
    matrix = [
        [row_dict['pattern_0_0'], row_dict['pattern_0_1'], row_dict['pattern_0_2']],
        [row_dict['pattern_1_0'], row_dict['pattern_1_1'], row_dict['pattern_1_2']],
        [row_dict['pattern_2_0'], row_dict['pattern_2_1'], row_dict['pattern_2_2']]
    ]
    out = {k: v for k, v in row_dict.items() if not k.startswith('pattern')}
    out['pattern_matrix'] = matrix
    return out

print("Quality A (Case 1):")
print(json.dumps(format_quality(get_row_as_dict(df[df['production_quality'] == 3], q_features)), indent=2))
print("Quality C (Case 2):")
print(json.dumps(format_quality(get_row_as_dict(df[df['production_quality'] == 1], q_features)), indent=2))
print("Quality D (Case 3):")
print(json.dumps(format_quality(get_row_as_dict(df[df['production_quality'] == 0], q_features)), indent=2))
