# Granular Agent Testing Instructions

This guide provides instructions for running the comprehensive test suite for the dynamic agent.

---

### **1. Environment Setup (Critical Prerequisite)**

The agent requires a valid Anthropic API key to function. You must configure this before running any tests.

1.  **Create a `.env` file** in the project's root directory.
2.  **Add your API key** to the `.env` file as follows, replacing the placeholder with your actual key:
    ```
    ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY_HERE"
    ```
3.  **Install Dependencies**: Ensure you have installed all necessary libraries, including `python-dotenv`.
    ```bash
    pip3 install -r requirements.txt 
    # (Assuming a requirements.txt file exists. If not, install libraries individually.)
    pip3 install python-dotenv langchain-anthropic
    ```

---

### **2. Running the Tests**

There are two primary test scripts:

*   **`testing/test_fixed_workflows.py`**: This script runs integration tests against predefined plans. It is useful for debugging the orchestrator's execution logic without relying on a live LLM for planning.
*   **`testing/run_single_e2e_test.py`**: This script runs a single, live end-to-end test. It is the definitive test of the agent's full capabilities.

**To run a test, execute the following command:**

```bash
# To run the integration tests
python3 testing/test_fixed_workflows.py

# To run the first E2E test (summarization)
python3 testing/run_single_e2e_test.py
```

---

### **3. Test Output**

The end-to-end test script will generate a JSON file for each test run in the `testing/e2e_results/` directory. This file contains the complete execution trace, including:

*   **`status`**: "success" or "error".
*   **`final_answer`**: The agent's final response to the user.
*   **`reasoning_log`**: A step-by-step log of the LLM's plan and the result of each tool call.

This output file is the primary artifact for analyzing the agent's performance. Refer to `TEST_RESULTS_ANALYSIS.md` for guidance on how to interpret these results.
