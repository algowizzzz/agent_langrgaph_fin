import requests
import json
import os
from datetime import datetime

# --- Configuration ---
BASE_URL = "http://localhost:8000"
SESSION_ID = "business-test-session-1"

# Define the test cases for the generate_without_context node
QNA_POD_TEST_CASES = {
    "generate_without_context": [
        {
            "id": "1.1.1",
            "description": "Simple Finance Query",
            "query": "What is the difference between debt and equity financing?",
        },
        {
            "id": "1.1.2",
            "description": "Complex Risk Management Query",
            "query": "Explain the concept of Value at Risk (VaR) and its main limitations in portfolio management.",
        },
        {
            "id": "1.1.3",
            "description": "Comparative Financial Analysis Query",
            "query": "Compare and contrast the Capital Asset Pricing Model (CAPM) with the Fama-French Three-Factor Model.",
        },
    ]
}

def run_qna_tests():
    """Runs tests for the Q&A Pod, specifically the generate_without_context node."""
    component_name = "generate_without_context"
    print(f"--- Running Tests for: {component_name} ---")

    # Create a directory for today's test results
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("business_testing", "test_results", today_str, component_name)
    os.makedirs(output_dir, exist_ok=True)

    test_cases = QNA_POD_TEST_CASES.get(component_name, [])

    for test in test_cases:
        test_id = test["id"]
        query = test["query"]
        print(f"  Running Test Case: {test_id} - {test['description']}")

        payload = {
            "session_id": SESSION_ID,
            "messages": [{"role": "user", "content": query}],
            "uploaded_files": {}
        }

        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes
            result = response.json()

            # Save the successful result
            output_path = os.path.join(output_dir, f"{test_id}_SUCCESS.json")
            with open(output_path, "w") as f:
                json.dump(result, f, indent=4)
            print(f"    ✅ SUCCESS: Result saved to {output_path}")

        except requests.exceptions.RequestException as e:
            error_message = {"error": str(e), "payload": payload}
            output_path = os.path.join(output_dir, f"{test_id}_FAILURE.json")
            with open(output_path, "w") as f:
                json.dump(error_message, f, indent=4)
            print(f"    ❌ FAILURE: {e}. Details saved to {output_path}")

    print(f"--- Finished Tests for: {component_name} ---\n")


if __name__ == "__main__":
    print("Starting Business-Focused Test Runner...")
    run_qna_tests()
    # In the future, we can add calls to other test functions here
    # e.g., run_document_loader_tests()
    print("All tests completed.")
