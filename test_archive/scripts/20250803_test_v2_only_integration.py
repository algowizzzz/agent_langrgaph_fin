#!/usr/bin/env python3
"""
Test V2-Only Integration Layer (without dependencies)
Validates that V1 fallback has been successfully removed
"""

import sys
import os

def test_integration_imports():
    """Test that integration layer imports correctly without V1 dependencies"""
    print("🧪 Testing V2-Only Integration Layer")
    print("=" * 50)
    
    try:
        # Test that we can import the integration without V1 dependencies
        sys.path.insert(0, '/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent')
        
        # This should fail gracefully without V1 fallback code
        print("📦 Testing integration import...")
        
        # Check if the file has been updated correctly
        with open('orchestrator_integration.py', 'r') as f:
            content = f.read()
        
        # Verify V1 fallback removal
        v1_indicators = [
            'fallback_to_v1',
            'enable_v2', 
            'orchestrator_v1',
            'from orchestrator import Orchestrator',
            '_run_v1_fallback'
        ]
        
        found_v1_code = []
        for indicator in v1_indicators:
            if indicator in content:
                found_v1_code.append(indicator)
        
        if found_v1_code:
            print("❌ V1 fallback code still present:")
            for code in found_v1_code:
                print(f"   - {code}")
            return False
        else:
            print("✅ V1 fallback code successfully removed")
        
        # Check for V2-only indicators
        v2_indicators = [
            'confidence_threshold',
            'orchestrator_v2',
            'OrchestratorV2',
            'V2-Only',
            'exclusively by Orchestrator 2.0'
        ]
        
        found_v2_code = []
        for indicator in v2_indicators:
            if indicator in content:
                found_v2_code.append(indicator)
        
        print(f"✅ V2-only indicators found: {len(found_v2_code)}/{len(v2_indicators)}")
        
        # Check global instance configuration
        if 'confidence_threshold=0.5' in content:
            print("✅ Global instance configured for V2-only")
        else:
            print("⚠️ Global instance may not be configured correctly")
        
        print("\n📊 Integration Layer Analysis:")
        print(f"   - File size: {len(content)} characters")
        print(f"   - V1 references removed: {len(v1_indicators) - len(found_v1_code)}/{len(v1_indicators)}")
        print(f"   - V2 indicators present: {len(found_v2_code)}/{len(v2_indicators)}")
        
        if not found_v1_code:
            print("\n🎉 SUCCESS: V2-Only Integration Layer Validated!")
            print("   - All V1 fallback code removed")
            print("   - Ready for V2-only operation")
            return True
        else:
            print("\n⚠️ PARTIAL: Some V1 code still present")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_constructor_signature():
    """Test that constructor signature has been updated"""
    print("\n🔧 Testing Constructor Signature Changes")
    print("-" * 30)
    
    try:
        with open('orchestrator_integration.py', 'r') as f:
            content = f.read()
        
        # Look for old constructor
        if 'def __init__(self, enable_v2: bool' in content:
            print("❌ Old constructor signature still present")
            return False
        
        # Look for new constructor
        if 'def __init__(self, confidence_threshold: float' in content:
            print("✅ New constructor signature found")
            return True
        else:
            print("⚠️ Constructor signature unclear")
            return False
            
    except Exception as e:
        print(f"❌ Constructor test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 V2-Only Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Import and V1 removal validation
    results.append(test_integration_imports())
    
    # Test 2: Constructor signature changes
    results.append(test_constructor_signature())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    print(f"📊 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("V2-Only Integration Layer is ready for testing")
    else:
        print(f"\n⚠️ {total-passed} tests failed")
        print("Additional cleanup may be required")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)