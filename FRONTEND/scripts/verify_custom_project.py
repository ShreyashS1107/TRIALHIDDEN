import urllib.request
import json
import sys

def test_custom_project_page():
    print("\n--- 1. Testing GET /custom-project page ---")
    url = "http://localhost:3000/custom-project"
    req = urllib.request.Request(url, headers={'User-Agent': 'PAIMANA-Test'})
    with urllib.request.urlopen(req, timeout=10) as res:
        print(f"Status: {res.status}")
        content = res.read().decode('utf-8')
        assert res.status == 200, "Expected status 200"
        assert "CUSTOM PROJECT ASSESSMENT" in content, "Missing page title"
        assert "Evaluate infrastructure project risk" in content, "Missing subheading"
        assert "01" in content and "PROJECT" in content, "Missing progressive steps"
        print("  [PASS] Page title, subtitle, and progressive step tracker present.")

def test_api_gateway_prediction():
    print("\n--- 2. Testing POST /api/predict/project (Next.js API Gateway) ---")
    url = "http://localhost:3000/api/predict/project"
    payload = {
        "project_name": "Bengaluru High-Speed Airport Metro Link",
        "project_id": "BMRCL-AIRPORT-LINK-01",
        "agency": "Ministry of Railways [MOR]",
        "state": "Karnataka",
        "original_cost_crore": 5600.0,
        "revised_cost_crore": 6450.0,
        "approval_start_date": "2023-01",
        "original_completion_date": "2026-12",
        "revised_completion_date": "2027-09",
        "physical_progress_percent": 34.0,
        "is_completed": False,
        "cumulative_expenditure_crore": 2200.0
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'PAIMANA-Test'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        print(f"Status: {res.status}")
        assert res.status == 200, "Expected status 200"
        data = json.loads(res.read().decode('utf-8'))
        print("Prediction Result Received:")
        print(f"  Project: {data['project_name']} (ID: {data['project_id']})")
        print(f"  Risk Band: {data['risk_band']}")
        print(f"  Integrated Risk: {data['selected_integrated_risk']}")
        print(f"  Schedule Delay Risk: {data['schedule_delay_risk']}")
        print(f"  Cost Overrun Risk: {data['cost_overrun_risk']}")
        print(f"  Predicted Final Cost: Rs. {data['predicted_cost_crore']} Cr")
        print(f"  Predicted Delay: +{data['predicted_delay_months']} Months")
        print(f"  Model Version: {data['model_version']}")
        print(f"  Risk Drivers Count: {len(data['risk_drivers'])}")

        assert "risk_band" in data, "Missing risk_band"
        assert "predicted_cost_crore" in data, "Missing predicted_cost_crore"
        assert len(data['risk_drivers']) >= 3, "Expected at least 3 risk drivers"
        print("  [PASS] API Gateway produced valid schema response.")

def test_fastapi_direct():
    print("\n--- 3. Testing Direct FastAPI Endpoint POST http://127.0.0.1:8000/predict/project ---")
    url = "http://127.0.0.1:8000/predict/project"
    payload = {
        "project_name": "Mumbai Trans-Harbour Freight Extension",
        "project_id": "MTHL-EXT-2026",
        "agency": "National Highways Authority of India [NHAI]",
        "state": "Maharashtra",
        "original_cost_crore": 3200.0,
        "revised_cost_crore": 3200.0,
        "approval_start_date": "2024-02",
        "original_completion_date": "2027-06",
        "physical_progress_percent": 65.0,
        "is_completed": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'PAIMANA-Test'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        print(f"Status: {res.status}")
        assert res.status == 200, "Expected status 200"
        data = json.loads(res.read().decode('utf-8'))
        print(f"  FastAPI Response: {data['project_name']} -> {data['risk_band']} ({data['selected_integrated_risk']})")
        assert data['project_id'] == "MTHL-EXT-2026", "Project ID mismatch"
        print("  [PASS] FastAPI microservice operational and responsive.")

def test_validation_failure():
    print("\n--- 4. Testing API Validation Guardrails (Negative Cost) ---")
    url = "http://localhost:3000/api/predict/project"
    payload = {
        "project_name": "Invalid Test",
        "project_id": "ERR-01",
        "agency": "NHAI",
        "state": "Delhi",
        "original_cost_crore": -50.0,  # INVALID NEGATIVE COST
        "revised_cost_crore": 100.0,
        "approval_start_date": "2024-01",
        "original_completion_date": "2026-01",
        "physical_progress_percent": 10.0
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=5)
        print("  [FAIL] Expected 400 Bad Request, but request succeeded.")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"  [PASS] Correctly rejected with HTTP {e.code}: {e.reason}")
        assert e.code == 400, "Expected HTTP 400"

if __name__ == "__main__":
    try:
        test_custom_project_page()
        test_api_gateway_prediction()
        test_fastapi_direct()
        test_validation_failure()
        print("\n==========================================")
        print("ALL CUSTOM PROJECT ASSESSMENT TESTS PASSED (100% PASS)")
        print("==========================================")
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
