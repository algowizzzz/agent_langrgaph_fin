#!/usr/bin/env python3
"""
Single Workflow Executor
Executes a single, specified workflow and saves detailed logs and responses.
"""

import asyncio
import os
import time
import uuid
import json
from collections import defaultdict

from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import upload_document

# --- Define the Workflow to Test ---

WORKFLOW_TO_TEST = {
    "workflow_1_csv_analysis": {
        "name": "📝 Conversational CSV Analysis",
        "description": "Tests upload, summary, calculation, visualization, and insights on a CSV file.",
        "documents": ["./test_documents/sample_data.csv"], 
        "requires_temp_data": True,
        "queries": [
            {
                "id": "1.1",
                "question": "I've uploaded employee salary data in {doc_names}. Please summarize what data we have.",
                "description": "Initial data summary"
            },
            {
                "id": "1.2",
                "question": "Now calculate the average salary by department.",
                "description": "Follow-up calculation"
            },
            {
                "id": "1.3",
                "question": "Create a bar chart showing the average salary by department.",
                "description": "Follow-up visualization"
            },
            {
                "id": "1.4",
                "question": "Based on this, what insights can you find?",
                "description": "Follow-up insights"
            }
        ]
    }
}

class SingleWorkflowTester:
    def __init__(self, workflow_id, workflow_details):
        self.workflow_id = workflow_id
        self.workflow_details = workflow_details
        self.integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
        
        # Setup logging directory
        self.run_timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"test_results_{self.workflow_id}_{self.run_timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log_file_path = os.path.join(self.output_dir, "run_log.txt")
        self.responses_file_path = os.path.join(self.output_dir, "responses.json")
        
        self.all_responses = []

    def log(self, message):
        """Log a message to both console and the log file."""
        print(message)
        with open(self.log_file_path, "a") as f:
            f.write(message + "\n")

    async def create_temp_csv(self):
        """Create a temporary employee salary CSV for testing."""
        csv_content = """employee_id,name,department,salary,experience_years,performance_rating
001,John Smith,Sales,52000,3,4.2
002,Jane Doe,Sales,48000,2,4.5
003,Bob Wilson,Marketing,55000,4,4.0
004,Alice Brown,Marketing,60000,5,4.3
005,Charlie Davis,IT,75000,6,4.8
"""
        os.makedirs("./test_documents", exist_ok=True)
        file_path = "./test_documents/sample_data.csv"
        with open(file_path, 'w') as f:
            f.write(csv_content)
        self.log(f"📄 Created temporary CSV at: {file_path}")
        return file_path

    async def run_workflow(self):
        """Execute the defined workflow and save the results."""
        self.log(f"🚀 STARTING WORKFLOW: {self.workflow_details['name']} 🚀")
        self.log("=" * 70)
        
        temp_csv_path = None
        if self.workflow_details.get("requires_temp_data"):
            temp_csv_path = await self.create_temp_csv()

        session_id = f"test_{self.workflow_id}_{uuid.uuid4().hex[:8]}"
        uploaded_doc_names = []

        try:
            # --- Document Upload Step ---
            if self.workflow_details.get("documents"):
                self.log(f"  📤 Uploading {len(self.workflow_details['documents'])} document(s)...")
                for doc_path in self.workflow_details["documents"]:
                    if not os.path.exists(doc_path):
                        self.log(f"    ❌ ERROR: Document not found at {doc_path}")
                        continue
                    
                    upload_result = await upload_document(doc_path, session_id)
                    if upload_result.get('status') == 'success':
                        doc_name = upload_result.get('doc_name')
                        uploaded_doc_names.append(doc_name)
                        self.log(f"    ✅ Uploaded: {doc_name}")
                    else:
                        self.log(f"    ❌ Upload failed for {doc_path}: {upload_result.get('message')}")
                
                if not uploaded_doc_names and self.workflow_details.get("documents"):
                     self.log("  ⚠️  No documents successfully uploaded. Skipping queries.")
                     return

            # --- Query Execution Step ---
            for query_info in self.workflow_details["queries"]:
                question = query_info["question"].format(doc_names=uploaded_doc_names)
                self.log(f"\n  ❓ Query {query_info['id']}: {query_info.get('description', question)}")
                self.log("  ⏳ Processing...")

                try:
                    result = await self.integration.run(
                        user_query=question,
                        session_id=session_id,
                        active_documents=uploaded_doc_names
                    )
                    self.all_responses.append({"query_id": query_info['id'], "response": result})
                    self.log_result(query_info['id'], result)

                except Exception as e:
                    self.log(f"    ❌ QUERY ERROR: {e}")
                    error_result = {"status": "error", "final_answer": str(e)}
                    self.all_responses.append({"query_id": query_info['id'], "response": error_result})
                    self.log_result(query_info['id'], error_result)
            
            # Save all responses to a file
            with open(self.responses_file_path, "w") as f:
                json.dump(self.all_responses, f, indent=4)
            self.log(f"\n💾 All responses saved to: {self.responses_file_path}")

        finally:
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)
        
        self.log("\n🎉 WORKFLOW EXECUTION COMPLETE 🎉")

    def log_result(self, query_id, result):
        """Log the result of a single query execution."""
        status = result.get('status', 'error')
        status_emoji = "✅" if status == 'success' else "❌"
        
        self.log(f"    {status_emoji} Status: {status.upper()} (v{result.get('orchestrator_version', '?')}, conf: {result.get('confidence_score', 0):.2f})")
        self.log(f"    📝 Response: {result.get('final_answer', 'No response')[:100]}...")


async def main():
    """Run the single workflow test."""
    workflow_id, workflow_details = list(WORKFLOW_TO_TEST.items())[0]
    tester = SingleWorkflowTester(workflow_id, workflow_details)
    await tester.run_workflow()

if __name__ == "__main__":
    asyncio.run(main())
