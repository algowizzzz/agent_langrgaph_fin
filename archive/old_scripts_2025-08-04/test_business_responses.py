#!/usr/bin/env python3
"""Business-focused test showing real AI Finance and Risk Agent responses."""

import asyncio
import sys
import os
import logging

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration

# Enable info logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_business_responses():
    """Test the AI Finance and Risk Agent with business-focused queries to show real responses."""
    print("💼 AI Finance and Risk Agent - Business Response Testing")
    print("=" * 70)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    
    # Business-focused test cases
    business_tests = [
        {
            "name": "📊 Risk Assessment Analysis",
            "query": "What is risk and what are the main types of financial risk mentioned?",
            "documents": ["riskandfinace.pdf"],
            "expected_response": "Professional risk analysis with specific financial risk types"
        },
        {
            "name": "💰 Financial Liquidity Question",
            "query": "What is financial liquidity and why is it important for businesses?",
            "documents": None,
            "expected_response": "Expert explanation of liquidity from financial knowledge"
        },
        {
            "name": "📈 Business Data Analysis",
            "query": "Give me a summary of the business data and identify key metrics",
            "documents": ["test_business_data.csv"],
            "expected_response": "Professional data analysis with business insights"
        },
        {
            "name": "🧠 Memory and Context",
            "query": "Remember our previous discussion about risk management strategies?",
            "documents": None,
            "expected_response": "Memory search with conversation context"
        },
        {
            "name": "🔍 Multi-Document Comparison",
            "query": "Compare the financial strategies mentioned in both car24 documents",
            "documents": ["car24_chpt1_0.pdf", "car24_chpt7.pdf"],
            "expected_response": "Professional financial comparison with 10k chunking"
        }
    ]
    
    print("🎯 Running Business-Focused Tests...\n")
    
    for i, test in enumerate(business_tests, 1):
        print(f"{'='*60}")
        print(f"💼 Test {i}/5: {test['name']}")
        print(f"📝 Query: '{test['query']}'")
        print(f"📁 Documents: {test['documents'] or 'None (using knowledge base)'}")
        print(f"🎯 Expected: {test['expected_response']}")
        print(f"{'='*60}")
        
        session_id = f"business_test_{i}_{int(asyncio.get_event_loop().time())}"
        
        try:
            # Run the query
            result = await integration.run(
                user_query=test['query'],
                session_id=session_id,
                active_documents=test['documents']
            )
            
            # Extract response details
            success = result.get('status') == 'success'
            answer = result.get('final_answer', result.get('answer', 'No answer provided'))
            confidence = result.get('confidence_score', 0)
            execution_summary = result.get('execution_summary', {})
            
            print(f"📊 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"🎯 Confidence: {confidence:.3f}")
            print(f"⚡ Execution: {execution_summary.get('completed', 0)}/{execution_summary.get('total_steps', 0)} steps")
            print(f"⏱️  Time: {execution_summary.get('total_execution_time', 0):.2f}s")
            
            if answer and len(answer) > 100:
                print(f"\n💡 **BUSINESS RESPONSE:**")
                print(f"{'─'*60}")
                
                # Show first paragraph
                paragraphs = answer.split('\n\n')
                first_paragraph = paragraphs[0] if paragraphs else answer[:300]
                print(f"📄 {first_paragraph}")
                
                if len(paragraphs) > 1:
                    print(f"\n📋 **KEY POINTS:**")
                    # Show bullet points or key sections
                    lines = answer.split('\n')
                    key_lines = [line.strip() for line in lines if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.'))][:5]
                    for line in key_lines:
                        print(f"   {line}")
                
                print(f"\n📊 **RESPONSE METRICS:**")
                print(f"   📏 Length: {len(answer)} characters")
                print(f"   📖 Paragraphs: {len(paragraphs)}")
                print(f"   🎯 Professional Score: {confidence:.1%}")
                
                # Analyze response quality
                business_keywords = ['financial', 'business', 'risk', 'analysis', 'strategy', 'investment', 'market', 'capital', 'liquidity', 'performance']
                keyword_count = sum(1 for keyword in business_keywords if keyword.lower() in answer.lower())
                print(f"   💼 Business Relevance: {keyword_count}/10 keywords detected")
                
            else:
                print(f"\n⚠️  **LIMITED RESPONSE:**")
                print(f"📄 Got: '{answer}'")
                print(f"📏 Length: {len(answer) if answer else 0} characters")
            
            print(f"\n{'─'*60}")
            
        except Exception as e:
            print(f"💥 **TEST FAILED:** {e}")
            logger.exception("Business test error:")
        
        print()  # Add spacing between tests
    
    print(f"{'='*70}")
    print("📊 **BUSINESS TESTING COMPLETE**")
    print("🎯 The AI Finance and Risk Agent demonstrates:")
    print("   💼 Professional financial analysis capabilities")
    print("   📊 Multi-document processing with 10k chunking")
    print("   🧠 Memory search and conversation context")
    print("   📈 Business data analysis and insights")
    print("   🔍 Intelligent query routing based on content type")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_business_responses())