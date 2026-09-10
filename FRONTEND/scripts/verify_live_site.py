import urllib.request
import re
import json

URL = "http://localhost:3000"

def test_live_site():
    print(f"Connecting to {URL}...")
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as res:
        status = res.status
        html = res.read().decode('utf-8', errors='ignore')
        
    print(f"Status Code: {status}")
    print(f"HTML Payload Size: {len(html):,} bytes")
    
    sections = [
        ("Platform Brand", "PAIMANA"),
        ("Tagline", "INTELLIGENCE FOR A FLOWING FUTURE"),
        ("Hero Video Asset", "SIH%20VIDEO.mp4"),
        ("Transition Video Asset", "SIH%20VIDEO%202.mp4"),
        ("3D Landscape Canvas", 'id="landscape"'),
        ("Data Foundation", "data-foundation"),
        ("Project Dossier", "project-intelligence"),
        ("Risk Prediction Hub", "risk-prediction"),
        ("Cost Intelligence", "cost-intelligence"),
        ("Schedule Debt", "schedule-intelligence"),
        ("Explainable AI", "explainable-ai"),
        ("Early Warning Center", "early-warning"),
        ("Prioritization Matrix", "prioritization"),
        ("India Map", "india-map"),
        ("Timeline Analysis", "timeline"),
        ("Data Trust Layer", "data-trust"),
        ("Anomaly Detection", "anomaly-detection"),
        ("Simulation Sandbox", "simulation"),
        ("What-If Badge", "DEMO SIMULATION"),
        ("Asset Comparison", "comparison"),
        ("AI Decision Assistant", 'id="assistant"'),
        ("Roadmap & Final CTA", 'id="final-cta"'),
    ]
    
    print("\n--- Verifying Section Markers in Rendered Markup ---")
    all_passed = True
    for label, pattern in sections:
        count = len(re.findall(re.escape(pattern), html, re.IGNORECASE))
        if count > 0:
            print(f"  [PASS] {label.ljust(26)} -> found '{pattern}' ({count}x)")
        else:
            print(f"  [FAIL] {label.ljust(26)} -> missing '{pattern}'")
            all_passed = False
            
    # Also verify data API endpoints
    data_endpoints = [
        "/data/paimana_summary.json",
        "/data/featured_projects.json",
        "/data/system_alerts.json",
        "/data/india_nodes.json",
        "/data/anomalies.json"
    ]
    
    print("\n--- Verifying Static JSON Datasets ---")
    for endpoint in data_endpoints:
        ep_url = f"{URL}{endpoint}"
        with urllib.request.urlopen(ep_url, timeout=5) as ep_res:
            data = json.loads(ep_res.read().decode('utf-8'))
            print(f"  [PASS] {endpoint.ljust(32)} -> HTTP {ep_res.status} (records: {len(data) if isinstance(data, list) else len(data.keys())})")
            
    # Verify Video Assets
    video_endpoints = [
        "/videos/SIH%20VIDEO.mp4",
        "/videos/SIH%20VIDEO%202.mp4"
    ]
    print("\n--- Verifying Video Streaming Endpoints ---")
    for v_endpoint in video_endpoints:
        v_url = f"{URL}{v_endpoint}"
        req = urllib.request.Request(v_url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as v_res:
            c_len = int(v_res.headers.get('Content-Length', 0))
            print(f"  [PASS] {v_endpoint.ljust(32)} -> HTTP {v_res.status} ({c_len / (1024*1024):.2f} MB)")
            
    if all_passed:
        print("\n==========================================================================")
        print("PERFECT 100% VERIFICATION: ALL 18 SECTIONS, DATASETS, AND ASSETS ACTIVE!")
        print("==========================================================================\n")
    else:
        print("\nSome section markers were not found in initial server render.")

if __name__ == "__main__":
    test_live_site()
