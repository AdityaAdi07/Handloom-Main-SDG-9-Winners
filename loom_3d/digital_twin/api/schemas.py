from pydantic import BaseModel
from typing import List, Optional

# --- REQUEST SCHEMAS ---

class DefectRequest(BaseModel):
    machine_speed: float
    thread_warp_tension: float
    thread_weft_tension: float
    environment_temperature: float
    environment_humidity: float
    environment_vibration: float
    energy_power: float
    pattern_matrix: List[List[int]]

class FaultRequest(BaseModel):
    machine_speed: float
    environment_vibration: float
    thread_warp_tension: float
    thread_weft_tension: float
    energy_power: float
    control_speed_error: float

class MaintenanceRequest(BaseModel):
    fault_anomaly_score: float
    environment_vibration: float
    energy_power: float
    machine_cycles: int
    fault_thread_break: int
    fault_motor_fault: int
    fault_overheat: int

class QualityRequest(BaseModel):
    thread_warp_tension: float
    thread_weft_tension: float
    machine_speed: float
    environment_humidity: float
    production_defect_rate: float
    pattern_matrix: List[List[int]]

# --- RESPONSE SCHEMAS ---

class DefectResponse(BaseModel):
    defect_rate: float

class FaultResponse(BaseModel):
    fault_prediction: str
    alert: Optional[str] = None

class MaintenanceResponse(BaseModel):
    maintenance_required: bool
    alert: Optional[str] = None

class QualityResponse(BaseModel):
    fabric_quality: str
