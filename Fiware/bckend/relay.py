from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

FIWARE_URL = "http://localhost:1026/v2/entities/loom_01"

@app.route('/twin')
def twin():
    try:
        res = requests.get(FIWARE_URL)
        return jsonify(res.json())
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(port=5050)