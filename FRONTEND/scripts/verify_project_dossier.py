import urllib.request
import re
import sys

def check_endpoint(url, checks):
    print(f"\n==========================================")
    print(f"Testing URL: {url}")
    print(f"==========================================")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PAIMANA-Test-Client'})
        with urllib.request.urlopen(req, timeout=10) as res:
            status = res.status
            content = res.read().decode('utf-8')
            print(f"Status Code: {status} (Bytes: {len(content)})")
            
            if status != 200:
                print(f"FAILED: Expected 200, got {status}")
                return False

            all_passed = True
            for check_name, pattern in checks.items():
                if isinstance(pattern, str):
                    found = pattern.lower() in content.lower()
                else:
                    found = bool(pattern.search(content))
                
                if found:
                    print(f"  [PASS] {check_name}")
                else:
                    print(f"  [FAIL] {check_name} (Pattern: {pattern})")
                    all_passed = False
            return all_passed
    except Exception as e:
        print(f"ERROR connecting to {url}: {e}")
        return False

kadapa_checks = {
    "Header - PROJECT INTELLIGENCE": "project intelligence",
    "Header - Project ID": "612786",
    "Header - Project Name": "Kadapa Airport",
    "Header - Agency": "Airport Authority of India",
    "Header - Back to Projects": "back to projects",
    "Pillars - WHAT IS HAPPENING": "1. what is happening?",
    "Pillars - WHY IS IT HAPPENING": "2. why is it happening?",
    "Pillars - WHAT WILL HAPPEN": "3. what will happen?",
    "Pillars - WHAT SHOULD WE WATCH": "4. what should we watch?",
    "Section 01 - PROJECT SNAPSHOT": "project snapshot",
    "Section 01 - Original Cost Rs 265.91": "265.91",
    "Section 01 - No revision recorded": "no revision recorded.",
    "Section 02 - COST TRAJECTORY": "cost trajectory",
    "Section 02 - Legend Cumulative Spend": "cumulative spend",
    "Section 03 - SCHEDULE TRAJECTORY": "schedule trajectory",
    "Section 04 - PHYSICAL PROGRESS": "physical progress over time",
    "Section 05 - ML RISK PREDICTION": "machine learning inference engine",
    "Section 05 - Cost Overrun Risk": "cost overrun risk",
    "Section 05 - Time Overrun Risk": "time overrun risk",
    "Section 05 - Overall Project Risk": "overall project risk",
    "Section 06 - RISK DRIVERS": "top risk drivers",
    "Section 06 - WHY IS THIS PROJECT AT RISK": "why is this project at risk?",
    "Section 07 - RISK TRAJECTORY OVER TIME": "risk trajectory over time",
    "Section 07 - Current Risk Score": "current risk score",
    "Section 08 - PROJECT LIFECYCLE TIMELINE": "project lifecycle timeline",
    "Section 09 - DATA PROVENANCE": "data provenance",
    "Section 09 - FlashReport_June_2026.pdf": "flashreport_june_2026.pdf",
    "Section 09 - Table 6: All Ongoing Projects": "table 6: all ongoing projects",
    "CTA - RUN WHAT-IF SIMULATION": "run what-if simulation",
    "CTA Link - /simulation?project=612786": "/simulation?project=612786"
}

sim_checks = {
    "Simulation Sandbox Header": "what if?",
    "Decision Support Counterfactual Engine": "decision-support counterfactual engine",
    "Back to Project link": "back to project intelligence"
}

passed1 = check_endpoint("http://localhost:3000/projects/612786", kadapa_checks)
passed2 = check_endpoint("http://localhost:3000/simulation?project=612786", sim_checks)

if passed1 and passed2:
    print("\nALL PROJECT INTELLIGENCE AND SIMULATION CHECKS PASSED (100% PASS)")
    sys.exit(0)
else:
    print("\nSOME CHECKS FAILED")
    sys.exit(1)
