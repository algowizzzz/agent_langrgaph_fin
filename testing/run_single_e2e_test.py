import asyncio
import os
import json
from datetime import datetime
import sys

# Add the project root to the path to allow importing the orchestrator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import Orchestrator
from dotenv import load_dotenv

# This script runs a single, targeted E2E test.

async def run_single_test(query: str, test_id: int):
    """Runs a single E2E test case."""
    print(f"--- 🚀 Starting E2E Test {test_id}: '{query}' ---")
    
    # Load environment variables from .env file
    load_dotenv()
    
    # 1. Setup: Define the test document
    test_doc_name = "e2e_test_document.txt"
    doc_content = """# Principled AI: A Framework for Ethical Technology

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
    with open(test_doc_name, "w") as f:
        f.write(doc_content)

    # 2. Initialize the orchestrator
    orchestrator = Orchestrator()

    # 3. Upload the document
    await orchestrator.tools['upload_document']['function'](test_doc_name)

    # 4. Run the query
    session_id = f"e2e-test-{test_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    result = await orchestrator.run(query, session_id)
    
    # 5. Save the results
    output_filename = f"testing/e2e_results/test_{test_id}_result.json"
    with open(output_filename, "w") as f:
        json.dump(result, f, indent=4)
            
    print(f"--- ✅ Test {test_id} complete. Results saved to {output_filename} ---")
    
    # 6. Cleanup
    if os.path.exists(test_doc_name):
        os.remove(test_doc_name)
    
    return result

if __name__ == "__main__":
    # Define the first test query
    query_to_test = "Summarize the entire document."
    test_id = 1
    
    # Run the test
    asyncio.run(run_single_test(query_to_test, test_id))
