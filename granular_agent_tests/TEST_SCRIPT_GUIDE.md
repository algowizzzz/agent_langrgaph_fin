# Guide to Testing Scripts

This document provides an overview of the different testing scripts available in this project and their specific purposes.

---

### 1. Unit Tests for Individual Tools
*   **Script**: `testing/test_tools.py`
*   **Purpose**: This is a classic unit test script that validates each individual tool (`upload_document`, `discover_document_structure`, `search_uploaded_docs`, `synthesize_content`) in complete isolation. It uses mock data to ensure that the fundamental building blocks of the agent are technically sound and reliable on their own.

---

### 2. Integration Tests for Predefined Workflows
*   **Script**: `testing/test_fixed_workflows.py`
*   **Purpose**: This script tests the agent's ability to execute a complete, multi-step workflow. It serves the purpose of what might traditionally be called a "node test" or a "graph test." Instead of using a live LLM to create a plan, it injects a *predefined* plan and validates that the orchestrator can correctly parse it, execute the sequence of tool calls, and hand off data between the steps. This is crucial for debugging the core orchestration logic.

---

### 3. End-to-End Tests (Live Agent)
There are two scripts for end-to-end testing:

*   **Script**: `testing/run_single_e2e_test.py`
    *   **Purpose**: This script is designed for debugging and targeted testing. It runs a single, specified query against the full, live agent, which uses the LLM to both generate and execute a plan.

*   **Script**: `testing/test_e2e_live_agent.py`
    *   **Purpose**: This is the final, comprehensive test script that runs the full suite of six business-critical queries against the live agent. It is the definitive validation of the agent's real-world performance. The detailed results of each run are saved to JSON files in the `testing/e2e_results/` directory for analysis.
