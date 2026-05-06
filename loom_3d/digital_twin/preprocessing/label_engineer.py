import pandas as pd

def create_labels(df):
    """
    Creates target labels for the models based on business rules.
    """
    print("Engineering labels...")
    
    # 1. CREATE maintenance_required label
    # maintenance_required = 1 IF anomaly_score > 0.7 OR severity == "high" OR motor_fault == True
    def check_maintenance(row):
        if row.get('fault_anomaly_score', 0) > 0.7:
            return 1
        if row.get('fault_detail_severity') == 'high':
            return 1
        if row.get('fault_motor_fault', False) == True:
            return 1
        return 0
        
    df['maintenance_required'] = df.apply(check_maintenance, axis=1)
    
    # 2. CREATE multi-class fault label for Fault Prediction Model
    # 0=no_fault, 1=thread_break, 2=overheat, 3=motor_fault
    def get_fault_class(row):
        # Prioritize higher severity faults if multiple exist (motor > overheat > thread)
        if row.get('fault_motor_fault', False):
            return 3
        elif row.get('fault_overheat', False):
            return 2
        elif row.get('fault_thread_break', False):
            return 1
        return 0
        
    df['fault_class'] = df.apply(get_fault_class, axis=1)
    
    print("Label engineering complete.")
    return df
