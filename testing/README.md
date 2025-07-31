# Testing Suite Documentation

This directory contains the full testing suite for the dynamic agent.

## How to Run Tests

### **IMPORTANT: Setup Your Environment**

Before running the live tests, you must provide your Anthropic API key.

1.  **Create a `.env` file** in the root directory of this project.
2.  **Add the following line** to the `.env` file, replacing the placeholder with your actual key:
    ```
    ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY_HERE"
    ```

The agent will automatically load this key to authenticate with the LLM.

---

### 1. Unit Tests
These tests validate each tool in isolation.

```bash
python3 -m unittest testing/test_tools.py
```

### 2. Integration Tests (Fixed Workflows)
These tests validate the orchestrator's ability to execute a predefined plan.

```bash
python3 testing/test_fixed_workflows.py
```

### 3. End-to-End Live Agent Tests
This is the final test that uses a live LLM to generate and execute plans.
**IMPORTANT:** Ensure you have completed the environment setup above.

```bash
python3 testing/test_e2e_live_agent.py
```
The results, including the full reasoning trace, will be saved in the `testing/e2e_results` directory.
