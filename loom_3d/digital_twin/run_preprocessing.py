import os
import pandas as pd
from preprocessing import load_and_flatten, create_labels, encode_features

def main():
    print("Starting Preprocessing Phase...")
    
    # Define paths
    input_file = os.path.join('data', 'loom_01_data_200k.json')
    output_file = os.path.join('data', 'processed_data.csv')
    
    if not os.path.exists(input_file):
        print(f"Error: Could not find dataset at {input_file}")
        print("Please ensure the dataset file is named 'loom_01_data_200k.json' and is located in the 'data' folder.")
        return
        
    # Step 1: Flatten
    df = load_and_flatten(input_file)
    
    # Step 2: Engineer Labels
    df = create_labels(df)
    
    # Step 3: Encode Features
    df = encode_features(df, registry_path='registry')
    
    # Save the processed dataset
    print(f"Saving processed data to {output_file}...")
    df.to_csv(output_file, index=False)
    print("Preprocessing pipeline completed successfully!")
    
if __name__ == "__main__":
    main()
