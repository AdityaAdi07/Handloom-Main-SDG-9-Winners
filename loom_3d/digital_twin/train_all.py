import os
import sys

# Add models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from train_defect import train_defect_model
from train_fault import train_fault_model
from train_maintenance import train_maintenance_model
from train_quality import train_quality_model

def main():
    print("========================================")
    print("   Starting Model Training Pipeline")
    print("========================================\n")
    
    # Run all model training pipelines
    train_defect_model()
    train_fault_model()
    train_maintenance_model()
    train_quality_model()
    
    print("========================================")
    print("   All Models Trained Successfully!")
    print("   Artifacts saved to registry/")
    print("========================================")

if __name__ == "__main__":
    main()
