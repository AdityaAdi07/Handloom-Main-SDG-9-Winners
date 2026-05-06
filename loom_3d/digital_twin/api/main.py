import sys
import os
import ast
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.schemas import (
    DefectRequest, DefectResponse, 
    FaultRequest, FaultResponse, 
    MaintenanceRequest, MaintenanceResponse, 
    QualityRequest, QualityResponse
)
from api.predict import InferenceEngine
from optimizer.optimizer import OptimizerEngine

app = FastAPI(
    title="Intelligent Digital Twin API",
    description="Strictly Isolated Endpoints for Prediction and Optimization",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inference_engine = None
optimizer_engine = None

@app.on_event("startup")
def load_engines():
    global inference_engine, optimizer_engine
    registry_path = os.path.join(os.path.dirname(__file__), '..', 'registry')
    inference_engine = InferenceEngine(registry_path=registry_path)
    optimizer_engine = OptimizerEngine(registry_path=registry_path)

# --- 1. DEFECT MODEL ---
@app.post("/predict/defect", response_model=DefectResponse)
def predict_defect(req: DefectRequest):
    try:
        rate = inference_engine.predict_defect(req)
        return {"defect_rate": round(rate, 4)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. FAULT MODEL ---
@app.post("/predict/fault", response_model=FaultResponse)
def predict_fault(req: FaultRequest):
    try:
        fault = inference_engine.predict_fault(req)
        alert = f"CRITICAL: {fault} detected!" if fault != "no_fault" else None
        return {"fault_prediction": fault, "alert": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. MAINTENANCE MODEL ---
@app.post("/predict/maintenance", response_model=MaintenanceResponse)
def predict_maintenance(req: MaintenanceRequest):
    try:
        maint = inference_engine.predict_maintenance(req)
        alert = "WARNING: Maintenance required soon." if maint else None
        return {"maintenance_required": maint, "alert": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4. QUALITY MODEL ---
@app.post("/predict/quality", response_model=QualityResponse)
def predict_quality(req: QualityRequest):
    try:
        quality = inference_engine.predict_quality(req)
        return {"fabric_quality": quality}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. OPTIMIZER ENGINE ---
@app.get("/optimize")
def get_best_settings(
    temperature: float = Query(32.0, description="Environment Temperature"),
    humidity: float = Query(65.0, description="Environment Humidity"),
    vibration: float = Query(0.05, description="Environment Vibration"),
    yarn_type: str = Query("silk", description="Yarn type (silk, cotton, polyester)"),
    pattern_matrix: str = Query("[[1,0,1],[0,1,0],[1,1,0]]", description="JSON string of 3x3 matrix")
):
    try:
        parsed_matrix = ast.literal_eval(pattern_matrix)
        env_data = {
            "temperature": temperature,
            "humidity": humidity,
            "vibration": vibration,
            "yarn_type": yarn_type,
            "pattern_matrix": parsed_matrix
        }
        return optimizer_engine.optimize(env_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
