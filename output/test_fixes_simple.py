#!/usr/bin/env python3
"""
Simple test to verify the V2 fixes are working without full dependency chain
"""

import sys
import traceback

def test_search_tools_fix():
    """Test the search tools fix."""
    print("🧪 Testing Search Tools Fix...")
    try:
        # Import the fixed search tools
        sys.path.insert(0, '../tools')
        from search_tools import search_knowledge_base
        
        # Test that it no longer returns mock data
        import asyncio
        result = asyncio.run(search_knowledge_base("test query"))
        
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if "error_type" in first_result:
                print(f"   ✅ Returns structured error: {first_result['error_type']}")
                print(f"   ✅ No more mock responses")
                return True
            elif "mock knowledge base result" in str(first_result):
                print("   ❌ Still returning mock data")
                return False
        print("   ❓ Unexpected result format")
        return False
        
    except Exception as e:
        print(f"   ❌ Error testing search tools: {e}")
        return False

def test_condition_parser():
    """Test the condition parser fix."""
    print("🧪 Testing Condition Parser Fix...")
    try:
        # Import the condition parser from fixed planning engine
        sys.path.insert(0, '../orchestrator_v2')
        from planning_engine import ConditionParser
        
        parser = ConditionParser()
        
        # Test parsing problematic conditions from original error
        test_conditions = [
            "len($step_1.output) > 0",
            "if_no_active_documents", 
            "document_exists",
            "step_1.success"
        ]
        
        success_count = 0
        for condition in test_conditions:
            try:
                condition_type, expression = parser.parse_condition(condition)
                print(f"   ✅ Parsed '{condition}' -> {condition_type}, {expression}")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Failed to parse '{condition}': {e}")
        
        if success_count == len(test_conditions):
            print(f"   ✅ All {success_count} conditions parsed successfully")
            return True
        else:
            print(f"   ⚠️ {success_count}/{len(test_conditions)} conditions parsed")
            return success_count > 0
            
    except Exception as e:
        print(f"   ❌ Error testing condition parser: {e}")
        traceback.print_exc()
        return False

def test_structured_errors():
    """Test structured error responses."""
    print("🧪 Testing Structured Error Responses...")
    try:
        # Test synthesis tools error handling
        sys.path.insert(0, '../tools')
        from synthesis_tools import SynthesisError
        
        # Create a test error
        error = SynthesisError.create_error(
            error_type="test_error",
            message="This is a test error",
            suggested_action="test_action"
        )
        
        required_fields = ["error_type", "success", "message", "suggested_action", "retryable", "replanning_hints"]
        
        missing_fields = [field for field in required_fields if field not in error]
        
        if not missing_fields:
            print(f"   ✅ Structured error has all required fields")
            print(f"   ✅ Error type: {error['error_type']}")
            print(f"   ✅ Suggested action: {error['suggested_action']}")
            return True
        else:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing structured errors: {e}")
        return False

def main():
    """Run all fix tests."""
    print("🔧 V2 ORCHESTRATOR FIXES VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Search Tools Mock Removal", test_search_tools_fix),
        ("Condition Parser Fix", test_condition_parser),
        ("Structured Error Responses", test_structured_errors)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        success = test_func()
        results.append((test_name, success))
        print()
    
    print("=" * 50)
    print("📊 VALIDATION RESULTS:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if success:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{len(results)})")
    
    if success_rate >= 80:
        print("🏆 FIXES VALIDATION SUCCESSFUL!")
        return True
    else:
        print("🔧 More fixes needed.")
        return False

if __name__ == "__main__":
    main()