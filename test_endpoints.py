import requests
import json
import time

URL = "http://127.0.0.1:8000"

def test_frontend_step():
    print("Testing /frontend_step with CORRECT Python code...", flush=True)
    res = requests.post(f"{URL}/frontend_step", json={
        "action_type": "paste_code", 
        "code": "print('Welcome to BugHunter AI!')", 
        "language": "python"
    })
    try:
        print("Status:", res.status_code)
        resp_json = res.json()
        print("Reward:", resp_json.get("reward"))
        print("Issues:", resp_json.get("issues"))
        print("Impact:", resp_json.get("impact"))
    except:
        print("Failed to connect or decode JSON")

    print("\n-------------------------------\n")
    print("Testing /frontend_step with WRONG Python code...", flush=True)
    res = requests.post(f"{URL}/frontend_step", json={
        "action_type": "paste_code", 
        "code": "print('Welcome to BugHunter AI!')wee", 
        "language": "python"
    })
    try:
        print("Status:", res.status_code)
        resp_json = res.json()
        print("Reward:", resp_json.get("reward"))
        print("Issues:", resp_json.get("issues"))
        print("Impact:", resp_json.get("impact"))
    except:
        print("Failed to connect or decode JSON")

if __name__ == "__main__":
    try:
        requests.get(f"{URL}/state", timeout=3)
        print("Backend is running! Proceeding with tests...\n")
        test_frontend_step()
    except:
        print("BACKEND IS NOT RUNNING. Please start uvicorn first.")
