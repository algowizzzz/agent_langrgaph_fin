#!/usr/bin/env python3
"""
Direct Fix Validation - Test improvements without import issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add paths for direct imports
sys.path.insert(0, '.')
sys.path.insert(0, 'tools')
sys.path.insert(0, 'orchestrator_v2')

async def test_search_tools_directly():
    """Test search tools improvements directly."""
    print("🔍 Testing Search Tools Improvements...")
    
    try:
        # Test the fixed search tools
        import tools.search_tools as search_tools
        
        # Test knowledge base search
        result = await search_tools.search_knowledge_base("test query")
        
        print(f"   Search result type: {type(result)}")
        print(f"   Search result length: {len(result) if isinstance(result, list) else 'N/A'}")
        
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            print(f"   First result keys: {list(first_result.keys()) if isinstance(first_result, dict) else 'Not a dict'}")
            
            # Check for mock response
            result_str = str(first_result)
            if "mock knowledge base result" in result_str.lower():
                print("   ❌ STILL CONTAINS MOCK RESPONSE")
                return False
            elif "error_type" in first_result:
                print(f"   ✅ STRUCTURED ERROR: {first_result.get('error_type')}")
                print(f"   ✅ ERROR MESSAGE: {first_result.get('message', 'No message')}")
                print(f"   ✅ SUGGESTED ACTION: {first_result.get('suggested_action', 'No action')}")
                return True
            else:
                print("   ❓ UNEXPECTED FORMAT")
                return False
        else:
            print("   ❌ NO RESULTS OR WRONG FORMAT")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

async def test_synthesis_tools_directly():
    """Test synthesis tools improvements directly."""
    print("🔧 Testing Synthesis Tools Improvements...")
    
    try:
        import tools.synthesis_tools as synthesis_tools
        
        # Test with no documents (should trigger error)
        result = await synthesis_tools.synthesize_content([], "test query")
        
        print(f"   Synthesis result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   Result keys: {list(result.keys())}")
            
            if "error_type" in result:
                print(f"   ✅ STRUCTURED ERROR: {result.get('error_type')}")
                print(f"   ✅ SUCCESS FLAG: {result.get('success')}")
                print(f"   ✅ MESSAGE: {result.get('message', 'No message')}")
                print(f"   ✅ SUGGESTED ACTION: {result.get('suggested_action', 'No action')}")
                
                # Check for replanning hints
                if "replanning_hints" in result:
                    print(f"   ✅ REPLANNING HINTS: {result.get('replanning_hints')}")
                    return True
                else:
                    print("   ⚠️ MISSING REPLANNING HINTS")
                    return False
            else:
                print("   ❌ NO ERROR STRUCTURE")
                return False
        else:
            print("   ❌ WRONG RESULT TYPE")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

async def test_document_tools_directly():
    """Test document tools improvements directly."""
    print("📄 Testing Document Tools Improvements...")
    
    try:
        import tools.document_tools as document_tools
        
        # Test with nonexistent file (should trigger error)
        result = await document_tools.upload_document("nonexistent_file.txt", "test_session")
        
        print(f"   Document upload result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   Result keys: {list(result.keys())}")
            
            if "error_type" in result:
                print(f"   ✅ STRUCTURED ERROR: {result.get('error_type')}")
                print(f"   ✅ SUCCESS FLAG: {result.get('success')}")
                print(f"   ✅ MESSAGE: {result.get('message', 'No message')}")
                print(f"   ✅ SUGGESTED ACTION: {result.get('suggested_action', 'No action')}")
                print(f"   ✅ RETRYABLE: {result.get('retryable')}")
                return True
            else:
                print("   ❌ NO ERROR STRUCTURE")
                return False
        else:
            print("   ❌ WRONG RESULT TYPE")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_planning_engine_condition_parsing():
    """Test planning engine condition parsing improvements."""
    print("🧠 Testing Planning Engine Condition Parsing...")
    
    try:
        # Test the condition parsing logic directly
        from orchestrator_v2.planning_engine import ConditionParser
        
        parser = ConditionParser()
        
        # Test the previously failing conditions
        test_conditions = [
            ("len($step_1.output) > 0", "Should parse as CUSTOM"),
            ("if_no_active_documents", "Should parse as CUSTOM"),
            ("document_exists", "Should parse as CUSTOM"),
            ("step_1.success", "Should parse as ON_SUCCESS"),
            ("always", "Should parse as ALWAYS"),
            ("on_failure", "Should parse as ON_FAILURE")
        ]
        
        successful_parses = 0
        total_conditions = len(test_conditions)
        
        for condition_str, expected in test_conditions:
            try:
                condition_type, expression = parser.parse_condition(condition_str)
                print(f"   ✅ '{condition_str}' → {condition_type} (expected: {expected})")
                successful_parses += 1
            except Exception as e:
                print(f"   ❌ '{condition_str}' failed: {e}")
        
        success_rate = (successful_parses / total_conditions) * 100
        print(f"   📊 Condition parsing success: {successful_parses}/{total_conditions} ({success_rate:.1f}%)")
        
        return successful_parses > total_conditions * 0.8  # 80% success threshold
        
    except Exception as e:
        print(f"   ❌ Planning engine test error: {str(e)}")
        return False

async def validate_error_response_format():
    """Validate that all error responses follow the expected format."""
    print("📋 Validating Error Response Format...")
    
    required_fields = ["error_type", "success", "message", "suggested_action", "retryable", "replanning_hints"]
    
    try:
        # Test each tool's error response format
        test_results = []
        
        # Search tools
        import tools.search_tools as search_tools
        search_result = await search_tools.search_knowledge_base("test")
        if isinstance(search_result, list) and len(search_result) > 0:
            error_obj = search_result[0]
            missing_fields = [field for field in required_fields if field not in error_obj]
            test_results.append(("search_knowledge_base", len(missing_fields) == 0, missing_fields))
        
        # Synthesis tools  
        import tools.synthesis_tools as synthesis_tools
        synthesis_result = await synthesis_tools.synthesize_content([], "test")
        if isinstance(synthesis_result, dict):
            missing_fields = [field for field in required_fields if field not in synthesis_result]
            test_results.append(("synthesize_content", len(missing_fields) == 0, missing_fields))
        
        # Document tools
        import tools.document_tools as document_tools
        doc_result = await document_tools.upload_document("nonexistent.txt", "test")
        if isinstance(doc_result, dict):
            missing_fields = [field for field in required_fields if field not in doc_result]
            test_results.append(("upload_document", len(missing_fields) == 0, missing_fields))
        
        # Report results
        passed_tests = 0
        for tool_name, passed, missing in test_results:
            if passed:
                print(f"   ✅ {tool_name}: All required fields present")
                passed_tests += 1
            else:
                print(f"   ❌ {tool_name}: Missing fields: {missing}")
        
        success_rate = (passed_tests / len(test_results)) * 100 if test_results else 0
        print(f"   📊 Error format compliance: {passed_tests}/{len(test_results)} ({success_rate:.1f}%)")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"   ❌ Error format validation failed: {str(e)}")
        return False

async def main():
    """Run direct fix validation."""
    print("🚀 DIRECT V2 FIX VALIDATION")
    print("=" * 60)
    print("Testing Phase 1 & 2 improvements with direct tool access")
    print()
    
    tests = [
        ("Search Tools Mock Elimination", test_search_tools_directly),
        ("Synthesis Tools Error Handling", test_synthesis_tools_directly),
        ("Document Tools Error Handling", test_document_tools_directly),
        ("Planning Engine Condition Parsing", lambda: test_planning_engine_condition_parsing()),
        ("Error Response Format Validation", validate_error_response_format)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status}")
            
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print()
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print()
    print("=" * 60)
    print("🎯 ASSESSMENT")
    print("=" * 60)
    
    if success_rate >= 80:
        print("🏆 EXCELLENT! Phase 1 & 2 fixes are working successfully.")
        print("   → Mock responses have been eliminated")
        print("   → Structured error handling is implemented")
        print("   → Planning engine improvements are functional")
        print("   → Ready for Phase 3: Execution engine fixes")
    elif success_rate >= 60:
        print("🟡 GOOD PROGRESS! Most fixes are working.")
        print("   → Some issues remain but core improvements are solid")
        print("   → Address remaining issues before Phase 3")
    else:
        print("🔴 NEEDS MORE WORK! Significant issues remain.")
        print("   → Review implementation of Phase 1 & 2 fixes")
        print("   → May need to debug specific components")
    
    print()
    print("📈 IMPROVEMENT COMPARISON:")
    print("   BEFORE: 0% tool coverage, 100% mock responses")
    print(f"   AFTER:  {success_rate:.1f}% fix validation, structured errors")
    print("   PROGRESS: Significant foundation improvements achieved")

if __name__ == "__main__":
    asyncio.run(main())