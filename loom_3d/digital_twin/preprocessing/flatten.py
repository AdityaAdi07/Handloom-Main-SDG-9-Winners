import pandas as pd

def load_and_flatten(filepath):
    """
    Loads JSONL dataset and flattens nested dictionaries and matrix.
    """
    import json
    print(f"Loading data from {filepath}...")
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping corrupted JSON on line {i+1}")
    df = pd.DataFrame(data)


    print("Flattening nested structures...")
    # Flatten nested dictionaries
    df = pd.json_normalize(df.to_dict(orient='records'))
    
    # Clean up column names by replacing dots with underscores
    df.columns = df.columns.str.replace('.', '_')
    
    # Flatten pattern_matrix (3x3 into 9 binary columns)
    if 'process_pattern_matrix' in df.columns:
        print("Flattening pattern_matrix...")
        # Expand matrix list into 9 individual columns
        for i in range(3):
            for j in range(3):
                col_name = f'pattern_{i}_{j}'
                df[col_name] = df['process_pattern_matrix'].apply(lambda x: x[i][j])
        df = df.drop(columns=['process_pattern_matrix'])
        
    # Drop unnecessary columns not useful for ML
    cols_to_drop = ['device_id', 'timestamp', 'process_pattern_id']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')
    
    print(f"Flattening complete. Shape: {df.shape}")
    return df
