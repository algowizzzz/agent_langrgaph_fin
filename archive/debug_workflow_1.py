#!/usr/bin/env python3
"""
Debug Script for Workflow 1: Conversational CSV Analysis
Executes the tool calls for the first workflow step-by-step to inspect
the inputs and outputs of each tool.
"""

import asyncio
import os
import uuid
import json

from tools.document_tools import upload_document, search_uploaded_docs
from tools.code_execution_tools import process_table_data, calculate_statistics
from tools.visualization_tools import create_chart

def print_step_result(step_name, result):
    """Helper function to print the results of a tool call."""
    print(f"\n--- Output from: {step_name} ---")
    if isinstance(result, dict):
        # Print dictionary keys and the type of their values for brevity
        for key, value in result.items():
            if isinstance(value, list) and value:
                print(f"  {key}: list of {len(value)} items, first item type: {type(value[0])}")
            elif isinstance(value, str) and len(value) > 150:
                 print(f"  {key}: str (length: {len(value)})")
            else:
                print(f"  {key}: {type(value)}")
    else:
        print(f"  Result Type: {type(result)}")
    
    # Save the full output to a file for detailed inspection
    output_filename = f"debug_{step_name}_output.json"
    with open(output_filename, "w") as f:
        try:
            json.dump(result, f, indent=4)
            print(f"  💾 Full output saved to: {output_filename}")
        except TypeError:
            f.write(str(result))
            print(f"  💾 Full output (as string) saved to: {output_filename}")
    print("-" * (len(step_name) + 24))


async def create_temp_csv():
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
    print(f"📄 Created temporary CSV at: {file_path}")
    return file_path

async def debug_csv_workflow():
    """Run the tool calls for the CSV workflow step-by-step."""
    print("🕵️‍♂️ STARTING DEBUG FOR WORKFLOW 1: CSV ANALYSIS 🕵️‍♂️")
    print("=" * 60)

    session_id = f"debug_session_{uuid.uuid4().hex[:8]}"
    temp_csv_path = await create_temp_csv()
    
    try:
        # --- Step 1: Upload Document ---
        upload_result = await upload_document(temp_csv_path, session_id)
        print_step_result("upload_document", upload_result)
        
        if upload_result.get("status") != "success":
            print("\n❌ Document upload failed. Aborting debug script.")
            return
            
        doc_name = upload_result.get("doc_name")

        # --- Step 2: Search Uploaded Document (to get content) ---
        search_result = await search_uploaded_docs(doc_name=doc_name, retrieve_full_doc=True)
        print_step_result("search_uploaded_docs", search_result)

        if not search_result:
            print("\n❌ Searching the document failed or returned no results. Aborting debug script.")
            return
        
        # The content is the list itself
        doc_content = search_result


        # --- Step 3: Process Table Data ---
        process_result = await process_table_data(table_data=doc_content, operation="summary")
        print_step_result("process_table_data", process_result)

        if process_result.get("status") != "success":
            print("\n❌ Processing table data failed. Aborting debug script.")
            return

        # --- Step 4 (Parallel): Calculate Statistics & Create Chart ---
        print("\n--- Executing Final Analysis Steps (Statistics and Chart) ---")
        
        # The processed data is in the 'processed_data' key
        processed_data_for_analysis = process_result.get("processed_data")

        # Calculate statistics
        stats_result = await calculate_statistics(data=processed_data_for_analysis, metrics=['mean', 'median', 'std'])
        print_step_result("calculate_statistics", stats_result)

        # Create a chart
        chart_result = await create_chart(data=processed_data_for_analysis, chart_type='bar', title='Salary by Department', x='department', y='salary')
        print_step_result("create_chart", chart_result)

    finally:
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)
            print(f"\n🗑️  Cleaned up temporary file: {temp_csv_path}")

    print("\n🕵️‍♂️ DEBUGGING COMPLETE 🕵️‍♂️")

if __name__ == "__main__":
    asyncio.run(debug_csv_workflow())
