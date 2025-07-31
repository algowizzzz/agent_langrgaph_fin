import asyncio
import os
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import Orchestrator

# This is the final, end-to-end test for the live agent.
# It uses the real orchestrator and a live LLM to generate and execute plans.
# The results, including the full reasoning trace, are saved to a JSON file.

# The 6 test queries we will run
TEST_QUERIES = [
    "Summarize the entire document.",
    "Summarize the 'Risk Factors' section only.",
    "Give me all the regulations as a bullet list from this document.",
    "Identify grammatical issues, list them, and write an improved version of the entire document.",
    "Do a deep research on everything related to 'wrong-way risk' in the document.",
    "Search the entire document for the mention of the word 'regulatory'."
]

# The document we will test against
TEST_DOC = "e2e_test_document.txt"
DOC_CONTENT = """# Principled AI: A Framework for Ethical Technology

## Section 1: Introduction
Artificial intelligence (AI) is transforming our world. This document outlines a framework for developing AI in a responsible and ethical manner. Our approach is built on fairness, accountability, and transparency. The regulatory landscape is evolving.

## Section 2: Core Principles
### Subsection 2.1: Fairness
AI systems must be designed to be impartial and avoid unfair bias. This is a complex challenge with no simple solution.

### Subsection 2.2: Accountability
There must be clear lines of responsibility for AI systems. This includes addressing any errors or unintended consequences. The grammar in this section could be improved.

### Subsection 2.3: Transparency
The decision-making processes of AI systems should be understandable to users and stakeholders. This is often called 'explainability'. A key risk is 'wrong-way risk', where a model's predictions are negatively correlated with outcomes.

## Section 3: Governance
We will establish an internal review board to oversee all AI projects. This ensures compliance with our ethical framework and with all relevant regulations.
"""

async def run_e2e_test():
    """Runs the full suite of E2E tests."""
    print("--- 🚀 Starting End-to-End Live Agent Test Suite ---")
    
    # 1. Setup: Create the test document
    with open(TEST_DOC, "w") as f:
        f.write(DOC_CONTENT)

    # 2. Initialize the orchestrator
    orchestrator = Orchestrator()

    # 3. Upload the document (a prerequisite for all other tests)
    print(f"\n--- Uploading test document: {TEST_DOC} ---")
    upload_result = await orchestrator.tools['upload_document']['function'](TEST_DOC)
    print(f"Upload result: {upload_result}")

    # 4. Run each test query
    for i, query in enumerate(TEST_QUERIES):
        session_id = f"e2e-test-{i+1}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"\n--- Running Test {i+1}/{len(TEST_QUERIES)}: '{query}' ---")
        
        result = await orchestrator.run(query, session_id)
        
        # 5. Save the results
        output_filename = f"testing/e2e_results/test_{i+1}_{query.replace(' ', '_')[:20]}.json"
        with open(output_filename, "w") as f:
            json.dump(result, f, indent=4)
            
        print(f"--- ✅ Test {i+1} complete. Results saved to {output_filename} ---")
        print(f"Final Answer: {result.get('final_answer', 'N/A')}")

    # 6. Cleanup
    if os.path.exists(TEST_DOC):
        os.remove(TEST_DOC)
    
    print("\n--- ✅ All End-to-End Tests Complete ---")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
