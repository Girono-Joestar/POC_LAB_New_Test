import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def test_health():
    print("🔍 Testing /api/health...")
    try:
        res = requests.get(f"{BASE_URL}/api/health")
        if res.status_code == 200:
            print("✅ Health OK:", res.json())
        else:
            print(f"❌ Health Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_list_experiments():
    print("🔍 Testing /api/experiments...")
    try:
        res = requests.get(f"{BASE_URL}/api/experiments")
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Found {len(data)} experiments")
            if len(data) > 0:
                print(f"   First exp: {data[0]['id']} - {data[0]['apparatus']}")
        else:
            print(f"❌ List Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_detail():
    print("🔍 Testing /api/experiments/MQC-01...")
    try:
        res = requests.get(f"{BASE_URL}/api/experiments/MQC-01")
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Detail OK: {data['apparatus']}")
            print(f"   Procedure steps: {len(data.get('procedure', []))}")
        else:
            print(f"❌ Detail Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Smoke Tests...")
    test_health()
    test_list_experiments()
    test_get_detail()
    print("🏁 Tests Over.")
