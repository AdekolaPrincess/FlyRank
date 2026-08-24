import json
import httpx

with open("evals/cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)

url = "http://127.0.0.1:8000/triage"
passed = 0
failed_cases = []

for i, case in enumerate(cases, start=1):
    response = httpx.post(url, json={"text": case["text"]}, timeout=60.0)
    result = response.json()
    actual_category = result.get("category")
    expected_category = case["expected_category"]

    if actual_category == expected_category:
        passed += 1
        print(f"Case {i}: PASS (expected {expected_category}, got {actual_category})")
    else:
        failed_cases.append({
            "case": i,
            "text": case["text"],
            "expected": expected_category,
            "actual": actual_category,
        })
        print(f"Case {i}: FAIL (expected {expected_category}, got {actual_category})")

print(f"\nScore: {passed}/{len(cases)}")
if failed_cases:
    print("\nFailed cases:")
    for fc in failed_cases:
        print(f"  Case {fc['case']}: \"{fc['text']}\" -> expected {fc['expected']}, got {fc['actual']}")