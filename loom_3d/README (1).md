# Intelligent Digital Twin for Handloom Machines

An advanced, machine learning-powered Digital Twin API for real-time monitoring, predictive maintenance, and autonomous optimization of handloom manufacturing processes.

---

## 🏗️ Project Architecture

This system has evolved from a basic Digital Twin into an **Intelligent Digital Twin**. Instead of a monolithic structure, the architecture strictly adheres to a "Separate Models by Purpose" design pattern. 

It exposes **5 distinct endpoints**: 4 dedicated to highly-targeted predictions, and 1 dedicated to simulation-based machine optimization.

### Project Structure
```text
digital_twin/
├── api/
│   ├── main.py            # FastAPI server and route definitions
│   ├── predict.py         # Inference Engine (loads and queries ML models)
│   └── schemas.py         # Pydantic schemas enforcing strict input/output boundaries
├── data/                  # Contains raw JSONL dataset and processed CSV
├── models/
│   ├── train_defect.py    # Training script for Model 1
│   ├── train_fault.py     # Training script for Model 2
│   ├── train_maintenance.py # Training script for Model 3
│   └── train_quality.py   # Training script for Model 4
├── optimizer/
│   └── optimizer.py       # Simulation-based grid search engine
├── preprocessing/         # Pipeline for flattening JSON, labeling, and encoding
├── registry/              # Saved model weights (.joblib) and encoders
├── train_all.py           # Master script to trigger all training pipelines
├── api_test_cases.md      # Payload cheat sheet for testing the API
└── README.md              # Project documentation
```

---

## 🧠 Machine Learning Models

We utilize **Random Forest** algorithms for their robustness against overfitting, ability to capture non-linear mechanical physics, and interpretability (feature importance).

To prevent "target leakage" and noisy inputs, every model was trained **only** on the variables that physically influence its target.

### 1. Defect Rate Prediction (Regression)
*   **Target:** `production.defect_rate` (Continuous)
*   **Method:** `RandomForestRegressor`
*   **Inputs:** Speed, Warp Tension, Weft Tension, Temperature, Humidity, Vibration, Power, Pattern Matrix.
*   **Purpose:** Predicts the continuous percentage of fabric defects based strictly on physical and environmental stress.

### 2. Fault Prediction (Multi-Class Classification)
*   **Target:** `fault_class` (`no_fault`, `thread_break`, `overheat`, `motor_fault`)
*   **Method:** `RandomForestClassifier` (using `class_weight='balanced'` to handle rare events)
*   **Inputs:** Speed, Vibration, Warp Tension, Weft Tension, Power, Speed Error.
*   **Purpose:** Diagnoses immediate mechanical failures based on stress and instability indicators.

### 3. Maintenance Prediction (Binary Classification)
*   **Target:** `maintenance_required` (Custom engineered label)
*   **Method:** `RandomForestClassifier` (using `class_weight='balanced_subsample'` for extreme minority classes)
*   **Inputs:** Anomaly Score, Vibration, Power, Machine Cycles, Fault Flags.
*   **Purpose:** Triggers maintenance alerts based on machine age (cycles), sustained anomalies, and recurring physical faults.

### 4. Fabric Quality Prediction (Ordinal Classification)
*   **Target:** `production.quality` (`A`, `B`, `C`, `D`)
*   **Method:** `RandomForestClassifier`
*   **Inputs:** Warp Tension, Weft Tension, Speed, Humidity, Pattern Matrix, and *Cascaded Defect Rate*.
*   **Purpose:** Grades the final physical output of the machine.

---

## ⚙️ The Optimizer Engine

The `/optimize` API is not a standard ML prediction model; it is a **Simulation-Based Optimization Engine**.

**How it works:**
1. Accepts fixed, uncontrollable environmental factors (Temperature, Humidity, Vibration) from the factory floor.
2. Generates a grid of hundreds of possible controllable machine settings (Speed: 80–150, Tensions: 4.0–8.0).
3. Simulates every combination by passing them through the **Defect Rate Regressor**.
4. Returns the exact combination of Speed and Tension that results in the absolute minimum expected defect rate.

---

## 🚀 How to Run the API

The backend is built with **FastAPI** for extreme performance and auto-generated documentation.

1. **Install Requirements:**
   Make sure you have installed the dependencies:
   ```bash
   pip install pandas numpy scikit-learn fastapi uvicorn pydantic joblib
   ```

2. **Start the Server:**
   Navigate to the project root and start the Uvicorn server:
   ```bash
   python api/main.py
   ```

3. **Access the Interactive UI:**
   Open your browser and navigate to:
   👉 **http://127.0.0.1:8000/docs**

Here, you can test all 5 endpoints interactively without writing any client code. Refer to `api_test_cases.md` for extreme payload examples guaranteed to trigger faults and alerts!
