import pandas as pd
import requests
import time
import json
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
FILE_PATH = "loom_01_data_200k.json"
ENTITY_ID = "loom_01"
BASE_URL = "http://localhost:1026/v2/entities"
ATTR_URL = f"{BASE_URL}/{ENTITY_ID}/attrs"

HEADERS = {"Content-Type": "application/json"}
DELAY = 0.2


# -----------------------------
# CREATE ENTITY
# -----------------------------
def create_entity():
    payload = {
        "id": ENTITY_ID,
        "type": "Loom"
    }

    res = requests.post(BASE_URL, json=payload, headers=HEADERS)

    if res.status_code == 201:
        print("✅ Entity created")
    elif res.status_code == 422:
        print("ℹ️ Entity already exists")
    else:
        print("❌ Entity creation error:", res.text)


# -----------------------------
# LOAD DATA
# -----------------------------
def load_data():
    print(f"Loading data from {FILE_PATH}...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    
    df = pd.json_normalize(data)

    print("Columns:", df.columns.tolist())
    print(f"Loaded {len(df)} rows")

    return df


# -----------------------------
# SAFE VALUE
# -----------------------------
def clean_value(val):
    if isinstance(val, (list, dict)):
        return str(val)
    if pd.isna(val):
        return None
    return val


# -----------------------------
# STREAM DATA (ALL COLUMNS)
# -----------------------------
def stream_data(df):
    cycle = 0

    while True:
        print(f"\n🔄 Cycle {cycle}")

        for i, row in tqdm(df.iterrows(), total=len(df)):

            payload = {}

            # ✅ SEND ALL COLUMNS
            for col in df.columns:
                val = clean_value(row.get(col))

                if val is None:
                    continue

                key = col.replace(".", "_")

                payload[key] = {"value": val}

            # ✅ IMPORTANT FIELDS (for 3D)
            payload["speed"] = {"value": float(row.get("machine.speed", 0))}
            payload["vibration"] = {"value": float(row.get("environment.vibration", 0))}
            payload["warp_tension"] = {"value": float(row.get("thread.warp_tension", 0))}
            payload["power"] = {"value": float(row.get("energy.power", 0))}
            payload["status"] = {"value": str(row.get("machine.status", "OFF"))}

            # 🔴 FAULT
            if row.get("fault.thread_break", False):
                payload["status"] = {"value": "FAULT"}

            try:
                res = requests.post(ATTR_URL, json=payload, headers=HEADERS)

                if res.status_code not in [201, 204]:
                    print("Error:", res.text)

                time.sleep(DELAY)

            except Exception as e:
                print("Exception:", e)

        cycle += 1


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    create_entity()
    df = load_data()
    stream_data(df)