from fastapi import APIRouter
import subprocess
import os
import json
from pipeline.config import ARTIFACTS_DIR

router = APIRouter()

@router.post("/trigger-pipeline")
def trigger_pipeline():
    """
    Manually trigger the data pipeline.
    """
    # In real app, consider using checking running status
    # subprocess.Popen(["python", "pipeline/collect_data.py"])
    return {"status": "Pipeline triggered"}

import sys
import datetime

@router.post("/retrain-model")
def retrain_model():
    """
    Manually trigger model retraining.
    """
    try:
        # Redirect output to log file
        log_path = os.path.join(ARTIFACTS_DIR, "pipeline.log")
        
        # Add a debug line to confirm we are writing to the file
        with open(log_path, "a") as f:
            f.write(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Triggering retraining via {sys.executable}...\n")

        with open(log_path, "a") as log_file:
            # We don't wait for completion here, just start it
            process = subprocess.Popen(
                [sys.executable, "-u", "-m", "pipeline.train_pipeline"], 
                stdout=log_file, 
                stderr=log_file
            )
        return {"status": "Retraining triggered", "pid": process.pid}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@router.get("/training-results")
def get_training_results():
    """
    Get the latest training comparison data (True vs Pred).
    """
    results_path = os.path.join(ARTIFACTS_DIR, "comparison_data.json")
    if not os.path.exists(results_path):
        return {"status": "No results found", "data": []}
    
    try:
        with open(results_path, "r") as f:
            data = json.load(f)
        return {"status": "Success", "data": data}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@router.get("/training-metrics")
def get_training_metrics():
    """
    Get the latest training metrics (RMSE, Accuracy, etc.).
    """
    metrics_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    if not os.path.exists(metrics_path):
        return {"status": "No metrics found", "data": []}
    
    try:
        with open(metrics_path, "r") as f:
            data = json.load(f)
        return {"status": "Success", "data": data}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@router.get("/logs")
def get_logs(lines: int = 50):
    """
    Get last N lines of logs.
    """
    log_path = os.path.join(ARTIFACTS_DIR, "pipeline.log")
    if not os.path.exists(log_path):
        return {"logs": ["Log file not found."]}
    
    try:
        with open(log_path, "r") as f:
            # Read all lines and take the last N
            all_lines = f.readlines()
            # Clean newlines
            logs = [line.strip() for line in all_lines[-lines:]]
        return {"logs": logs}
    except Exception as e:
        return {"logs": [f"Error reading log: {str(e)}"]}
