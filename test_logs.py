import requests
import uuid
import datetime
import random
import os

# To test this, you first need an API key from a logged-in user's dashboard.
# Once you have the key, set it as an environment variable or paste it below.
API_KEY = os.environ.get("LOG_API_KEY", "")
URL = "http://127.0.0.1:8000/api/logs/ingest/"

def generate_logs(count=1000, error_rate=0.05, start_time=None):
    if not start_time:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
    logs = []
    for i in range(count):
        # Simulate logs spread over the last 1 hour
        offset = random.randint(0, 3600)
        timestamp = start_time - datetime.timedelta(seconds=offset)
        
        is_error = random.random() < error_rate
        level = "ERROR" if is_error else "INFO"
        message = "Database timeout" if is_error else "User logged in successfully"
        
        logs.append({
            "timestamp": timestamp.isoformat(),
            "level": level,
            "message": message,
            "raw_data": {"user_id": random.randint(1, 1000), "ip": "192.168.1.1"}
        })
    return logs

if __name__ == "__main__":
    if not API_KEY:
        print("Please set the LOG_API_KEY environment variable to your Project API Key.")
        exit(1)
        
    print(f"Generating 10,000 background logs...")
    batch_1 = generate_logs(10000, error_rate=0.01) # 1% error rate historically
    
    print(f"Sending historical batch...")
    response = requests.post(URL, json=batch_1, headers={"X-API-KEY": API_KEY})
    print("Historical Response:", response.status_code, response.json())
    
    print("\nSimulating an attack / anomaly (spike in errors in the last 2 minutes)...")
    now = datetime.datetime.now(datetime.timezone.utc)
    batch_2 = []
    for _ in range(50):
        batch_2.append({
            "timestamp": now.isoformat(),
            "level": "ERROR",
            "message": "Out of memory error in worker",
            "raw_data": {"worker_id": "w-10"}
        })
        
    response = requests.post(URL, json=batch_2, headers={"X-API-KEY": API_KEY})
    print("Anomaly Response:", response.status_code, response.json())
    
    print("\nLogs ingested successfully!")
    print("Now run: python manage.py detect_anomalies to see the engine in action.")
