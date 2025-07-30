import asyncio
import json
import os
import sys
from datetime import datetime
import logging
from typing import Dict, Any

# --- Setup Python Path ---
# Add the project root directory to the Python path to allow imports from the main app
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- IMPORTANT ---
# Import the live pod objects from the application code for direct testing.
from qna_pod import qna_pod
from document_analysis_pod import document_analysis_pod
from document_processor import document_processor

# --- Test Configuration ---
RESULTS_DIR = os.path.join("business_testing", "isolated_test_results")
TEST_FILES_DIR = os.path.join("business_testing", "isolated_test_files")

# --- Helper Function ---
def save_test_result(node_name: str, test_id: str, output: Dict[str, Any], status: str = "SUCCESS"):
    """Saves the output of a test to a structured directory."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(RESULTS_DIR, today_str, node_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean up non-serializable objects before saving
    if 'doc_chunks' in output:
        # Convert Document objects to a serializable format (dictionaries)
        output['doc_chunks'] = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in output['doc_chunks']
        ]
    if 'uploaded_files' in output and output['uploaded_files']:
        output['uploaded_files'] = {k: v.dict() for k, v in output['uploaded_files'].items()}
    
    file_path = os.path.join(output_dir, f"{test_id}_{status}.json")
    with open(file_path, "w") as f:
        json.dump(output, f, indent=4)
    logging.info(f"✅ Result for '{node_name}' ({test_id}) saved to {file_path}")

# --- Test Functions ---

async def test_qna_pod_nodes():
    """Runs isolated tests for all nodes in the Q&A Pod."""
    node_name_general = "_generate_general_answer"
    logging.info(f"--- Running Isolated Test for: {node_name_general} ---")
    
    # Test Case 1: General Knowledge Query
    input_state_1 = {"question": "What is Value at Risk (VaR)?"}
    try:
        output_state_1 = await qna_pod._generate_general_answer(input_state_1)
        save_test_result(node_name_general, "QNA-1.1-VaR", output_state_1)
    except Exception as e:
        logging.error(f"Test QNA-1.1-VaR failed for {node_name_general}", exc_info=True)
        save_test_result(node_name_general, "QNA-1.1-VaR", {"error": str(e)}, "FAILURE")

    logging.info(f"--- Finished Isolated Test for: {node_name_general} ---\n")

async def test_doc_analysis_pod_nodes():
    """Runs isolated tests for all nodes in the Document Analysis Pod."""
    
    # --- Test _load_documents Node ---
    node_name_load = "_load_documents"
    logging.info(f"--- Running Isolated Test for: {node_name_load} ---")
    doc_objects = []  # Ensure this is initialized
    try:
        # The 'document_processor' is the modern helper for loading.
        processing_result = await document_processor.process_document(
            os.path.join(TEST_FILES_DIR, "hermes_strategy.txt")
        )
        if not processing_result.success:
            raise Exception(f"Document processing failed: {processing_result.error}")
        
        # We save the actual Document objects to pass to the next step
        doc_objects = processing_result.documents
        output_state_load = {"doc_chunks": doc_objects}
        save_test_result(node_name_load, "DOC-LOAD-1.1-TXT", output_state_load)
    except Exception as e:
        logging.error(f"Test DOC-LOAD-1.1-TXT failed for {node_name_load}", exc_info=True)
        save_test_result(node_name_load, "DOC-LOAD-1.1-TXT", {"error": str(e)}, "FAILURE")
    
    logging.info(f"--- Finished Isolated Test for: {node_name_load} ---\n")

    # This output becomes the input for the next tests
    # CRITICAL FIX: Pass the actual Document objects, not just the text content
    state_after_load = {"doc_chunks": doc_objects}

    # --- Test _planner_node Node ---
    node_name_plan = "_planner_node"
    logging.info(f"--- Running Isolated Test for: {node_name_plan} ---")
    input_state_plan = {
        "user_query": "Summarize the key points and action items.",
        "template_instructions": "",
        **state_after_load
    }
    try:
        output_state_plan = await document_analysis_pod._planner_node(input_state_plan)
        save_test_result(node_name_plan, "DOC-PLAN-1.1-Summary", output_state_plan)
    except Exception as e:
        logging.error(f"Test DOC-PLAN-1.1-Summary failed for {node_name_plan}", exc_info=True)
        save_test_result(node_name_plan, "DOC-PLAN-1.1-Summary", {"error": str(e)}, "FAILURE")
    
    logging.info(f"--- Finished Isolated Test for: {node_name_plan} ---\n")
    
    state_after_plan = output_state_plan

    # --- Test _executor_node Node ---
    node_name_exec = "_executor_node"
    logging.info(f"--- Running Isolated Test for: {node_name_exec} ---")
    input_state_exec = {
        **state_after_load,
        "planner_prompts": state_after_plan.get("planner_prompts", {})
    }
    try:
        output_state_exec = await document_analysis_pod._executor_node(input_state_exec)
        save_test_result(node_name_exec, "DOC-EXEC-1.1-Summary", output_state_exec)
    except Exception as e:
        logging.error(f"Test DOC-EXEC-1.1-Summary failed for {node_name_exec}", exc_info=True)
        save_test_result(node_name_exec, "DOC-EXEC-1.1-Summary", {"error": str(e)}, "FAILURE")

    logging.info(f"--- Finished Isolated Test for: {node_name_exec} ---\n")
    
    state_after_exec = output_state_exec

    # --- Test _synthesizer_node Node ---
    node_name_synth = "_synthesizer_node"
    logging.info(f"--- Running Isolated Test for: {node_name_synth} ---")
    input_state_synth = {
        "user_query": "Summarize the key points and action items.",
        "final_analysis": state_after_exec.get("final_analysis", "")
    }
    try:
        output_state_synth = await document_analysis_pod._synthesizer_node(input_state_synth)
        save_test_result(node_name_synth, "DOC-SYNTH-1.1-Summary", output_state_synth)
    except Exception as e:
        logging.error(f"Test DOC-SYNTH-1.1-Summary failed for {node_name_synth}", exc_info=True)
        save_test_result(node_name_synth, "DOC-SYNTH-1.1-Summary", {"error": str(e)}, "FAILURE")

    logging.info(f"--- Finished Isolated Test for: {node_name_synth} ---\n")


async def main():
    """Main function to run all isolated tests."""
    print("Starting Isolated Test Runner...")
    await test_qna_pod_nodes()
    await test_doc_analysis_pod_nodes()
    print("All isolated tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
