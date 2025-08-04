#!/usr/bin/env python3
"""
Debug script to trace data flow between orchestrator steps
"""

import asyncio
import json
from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import search_multiple_docs

async def debug_step_data_flow():
    """Debug what data flows between search and synthesis steps."""
    
    print("🔍 DEBUGGING STEP DATA FLOW")
    print("=" * 50)
    
    # First, see what search_multiple_docs actually returns
    print("\n📄 Step 1: Direct search_multiple_docs output")
    print("-" * 30)
    
    doc_names = [
        '20250801_231927_e702b3a7-5cbd-4557-b46b-9d352384f3ac_car24_chpt1_0.pdf',
        '20250801_231934_cb90fddd-c3b9-4a48-8bba-d55d28f0a3b0_car24_chpt7.pdf'
    ]
    
    direct_search_result = await search_multiple_docs(doc_names, query='compare')
    print(f"Type: {type(direct_search_result)}")
    print(f"Length: {len(direct_search_result)}")
    print(f"First item type: {type(direct_search_result[0]) if direct_search_result else 'N/A'}")
    print(f"First item keys: {list(direct_search_result[0].keys()) if direct_search_result and isinstance(direct_search_result[0], dict) else 'N/A'}")
    
    # Now let's monkey-patch the orchestrator to capture what it's actually passing
    print("\n🎯 Step 2: Orchestrator step output capture")
    print("-" * 30)
    
    # Store original synthesis function
    from tools.synthesis_tools import synthesize_content
    original_synthesize = synthesize_content
    captured_data = {}
    
    # Create wrapper to capture inputs
    async def capture_synthesize_input(documents, query, synthesis_type="summary"):
        captured_data['documents'] = documents
        captured_data['query'] = query
        captured_data['synthesis_type'] = synthesis_type
        captured_data['documents_type'] = type(documents)
        captured_data['documents_length'] = len(documents) if hasattr(documents, '__len__') else 'No length'
        
        print(f"  📥 Synthesis received:")
        print(f"     Documents type: {type(documents)}")
        print(f"     Documents length: {len(documents) if hasattr(documents, '__len__') else 'No length'}")
        
        if isinstance(documents, list) and len(documents) > 0:
            print(f"     First doc type: {type(documents[0])}")
            if isinstance(documents[0], dict):
                print(f"     First doc keys: {list(documents[0].keys())}")
        
        # Call original function
        return await original_synthesize(documents, query, synthesis_type)
    
    # Apply monkey patch
    import tools.synthesis_tools
    tools.synthesis_tools.synthesize_content = capture_synthesize_input
    
    # Run orchestrator
    integration = OrchestratorIntegration()
    
    try:
        result = await integration.orchestrator_v2.execute_query(
            user_query='Compare these two documents',
            session_id='debug_data_flow',
            active_documents=doc_names
        )
        
        print(f"\n📊 Orchestrator completed:")
        print(f"   Confidence: {result.get('confidence_score', 0):.3f}")
        
        if captured_data:
            print(f"\n📋 Captured synthesis input:")
            for key, value in captured_data.items():
                if key != 'documents':  # Don't print full documents
                    print(f"   {key}: {value}")
                else:
                    print(f"   documents: {type(value)} with {len(value) if hasattr(value, '__len__') else 'unknown'} items")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        # Restore original function
        tools.synthesis_tools.synthesize_content = original_synthesize

if __name__ == "__main__":
    asyncio.run(debug_step_data_flow())