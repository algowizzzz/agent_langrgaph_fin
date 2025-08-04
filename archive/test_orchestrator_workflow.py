#!/usr/bin/env python3
"""
Test Complete Orchestrator Workflow
Tests the end-to-end CSV → Python → Visualization workflow through the orchestrator
"""

import asyncio
import tempfile
import os
import json

# Import orchestrator
from orchestrator_integration import OrchestratorIntegration

async def test_orchestrator_csv_workflow():
    """Test the complete CSV workflow through orchestrator"""
    print("🎯 TESTING ORCHESTRATOR CSV WORKFLOW")
    print("=" * 50)
    
    # Initialize orchestrator
    integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
    session_id = "orchestrator_csv_test"
    
    # Create test CSV file
    csv_content = """department,employee,salary,experience
Sales,John,50000,2
Sales,Jane,48000,1
Marketing,Bob,55000,3
Marketing,Alice,52000,2
IT,Charlie,70000,5
IT,Diana,68000,4
Finance,Frank,60000,3
Finance,Grace,58000,2"""
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_file.write(csv_content)
    temp_file.close()
    
    print(f"📄 Created test CSV: {os.path.basename(temp_file.name)}")
    print("📋 Sample data:")
    print(csv_content[:100] + "...")
    
    try:
        # Step 1: Upload the CSV file first
        print("\n🔄 Step 1: Uploading CSV file")
        from tools.document_tools import upload_document
        upload_result = await upload_document(temp_file.name, session_id)
        
        if upload_result.get('status') == 'success':
            doc_name = upload_result.get('doc_name')
            print(f"✅ CSV uploaded as: {doc_name}")
        else:
            print(f"❌ Upload failed: {upload_result}")
            return
        
        # Step 2: Test different types of questions through orchestrator
        test_queries = [
            {
                "question": "Calculate the average salary by department and show me the results",
                "description": "Basic calculation request"
            },
            {
                "question": "Create a bar chart showing average salary by department",
                "description": "Visualization request"
            },
            {
                "question": "What is the salary distribution? Show me a statistical plot",
                "description": "Statistical analysis request"
            },
            {
                "question": "Calculate statistics for the salary data and create a word cloud of the departments",
                "description": "Multi-tool request"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}: {test_case['description']}")
            print(f"❓ Question: {test_case['question']}")
            print("⏳ Processing through orchestrator...")
            
            try:
                # Run query through orchestrator
                result = await integration.run(
                    user_query=test_case['question'],
                    session_id=session_id,
                    active_documents=[doc_name]
                )
                
                # Analyze result
                if result.get('status') == 'success':
                    answer = result.get('final_answer', '')
                    version = result.get('orchestrator_version', 'unknown')
                    confidence = result.get('confidence_score', 0)
                    
                    print(f"✅ SUCCESS (v{version}, confidence: {confidence:.2f})")
                    print(f"📝 Answer preview: {answer[:150]}...")
                    
                    # Check if visualization was created (look for base64 image indicators)
                    if 'image' in answer.lower() or 'chart' in answer.lower() or 'plot' in answer.lower():
                        print("🎨 Visualization appears to be included")
                    
                else:
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
            
            # Wait between tests
            await asyncio.sleep(2)
        
        print("\n" + "=" * 50)
        print("📊 ORCHESTRATOR WORKFLOW TEST COMPLETE")
        print("=" * 50)
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except:
            pass

async def test_simple_orchestrator_request():
    """Test a simple request to verify orchestrator is working"""
    print("\n🔍 TESTING SIMPLE ORCHESTRATOR REQUEST")
    print("=" * 50)
    
    integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
    
    # Simple question that should work with existing document
    simple_query = "What is finance and what is risk? Explain the difference."
    
    try:
        result = await integration.run(
            user_query=simple_query,
            session_id="simple_test",
            active_documents=["riskandfinance.pdf"]  # Use existing document
        )
        
        if result.get('status') == 'success':
            print("✅ Simple orchestrator request: SUCCESS")
            print(f"🔧 Version: {result.get('orchestrator_version', 'unknown')}")
            print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"📝 Answer: {result.get('final_answer', '')[:200]}...")
        else:
            print("❌ Simple orchestrator request: FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Simple orchestrator request: ERROR - {e}")

if __name__ == "__main__":
    async def main():
        await test_simple_orchestrator_request()
        await test_orchestrator_csv_workflow()
    
    asyncio.run(main())