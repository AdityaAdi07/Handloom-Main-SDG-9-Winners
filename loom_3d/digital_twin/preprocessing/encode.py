import pandas as pd
import joblib
import os
from sklearn.preprocessing import LabelEncoder

def encode_features(df, registry_path='../registry'):
    """
    Encodes categorical features and quality labels.
    """
    print("Encoding features...")
    
    os.makedirs(registry_path, exist_ok=True)
    
    # 1. yarn_type -> LabelEncoder (silk=0, cotton=1, polyester=2)
    if 'thread_yarn_type' in df.columns:
        # Custom mapping to match the spec precisely
        yarn_map = {'silk': 0, 'cotton': 1, 'polyester': 2}
        df['thread_yarn_type_encoded'] = df['thread_yarn_type'].map(yarn_map).fillna(0).astype(int)
        
        # We also fit a LabelEncoder to save it to registry just in case API needs it
        # Note: LabelEncoder assigns alphabetically: cotton=0, polyester=1, silk=2
        # So we create a dummy class to emulate our mapping if strictly needed,
        # but storing the dict in API code is often easier. Let's just store the dict.
        joblib.dump(yarn_map, os.path.join(registry_path, 'yarn_encoder.joblib'))
        
        # Drop original column and rename encoded to original name for models
        df = df.drop(columns=['thread_yarn_type'])
        df = df.rename(columns={'thread_yarn_type_encoded': 'thread_yarn_type'})
        
    # 2. control.mode -> Binary (AUTO=1, MANUAL=0)
    if 'control_mode' in df.columns:
        mode_map = {'AUTO': 1, 'MANUAL': 0}
        df['control_mode'] = df['control_mode'].map(mode_map).fillna(1).astype(int)
        
    # 3. quality -> OrdinalEncoder (A=3, B=2, C=1, D=0)
    if 'production_quality' in df.columns:
        quality_map = {'A': 3, 'B': 2, 'C': 1, 'D': 0}
        df['production_quality_encoded'] = df['production_quality'].map(quality_map).fillna(0).astype(int)
        joblib.dump(quality_map, os.path.join(registry_path, 'quality_encoder.joblib'))
        
        # Drop original and rename
        df = df.drop(columns=['production_quality'])
        df = df.rename(columns={'production_quality_encoded': 'production_quality'})
        
    # 4. Process all boolean columns (fault flags) to integers (0/1)
    bool_cols = [col for col in df.columns if df[col].dtype == bool]
    for col in bool_cols:
        df[col] = df[col].astype(int)
        
    print("Encoding complete.")
    return df
