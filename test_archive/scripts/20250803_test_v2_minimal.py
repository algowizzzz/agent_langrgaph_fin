#!/usr/bin/env python3
"""
Minimal V2-Only System Test
Tests basic V2 functionality without requiring full orchestrator initialization
"""

import os
import sys
from dotenv import load_dotenv

def test_environment_setup():
    """Test that environment is set up correctly"""
    print("🔧 Testing Environment Setup")
    print("-" * 30)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✅ ANTHROPIC_API_KEY configured (length: {len(api_key)})")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY not found")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("\n📦 Testing Module Imports")
    print("-" * 30)
    
    imports_to_test = [
        ("langchain_anthropic", "ChatAnthropic"),
        ("langchain", "text_splitter"),
        ("tools.document_tools", "upload_document"),
        ("tools.synthesis_tools", "synthesize_content"),
        ("pandas", "DataFrame"),
        ("matplotlib", "pyplot"),
        ("wordcloud", "WordCloud"),
        ("numpy", "array")
    ]
    
    success_count = 0
    for module, component in imports_to_test:
        try:
            if component:
                exec(f"from {module} import {component}")
            else:
                exec(f"import {module}")
            print(f"✅ {module}.{component if component else ''}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}.{component if component else ''}: {e}")
        except Exception as e:
            print(f"⚠️ {module}.{component if component else ''}: {e}")
    
    print(f"\n📊 Import Success: {success_count}/{len(imports_to_test)}")
    return success_count == len(imports_to_test)

def test_orchestrator_integration_import():
    """Test that we can import the V2-only integration"""
    print("\n🚀 Testing V2-Only Orchestrator Integration")
    print("-" * 30)
    
    try:
        # This might fail due to missing V2 orchestrator, but we want to see the specific error
        from orchestrator_integration import OrchestratorIntegration
        print("✅ OrchestratorIntegration imported successfully")
        
        # Try to create instance (this will likely fail, but let's see why)
        integration = OrchestratorIntegration(confidence_threshold=0.5)
        print("✅ OrchestratorIntegration instance created")
        
        # Get system status
        status = integration.get_system_status()
        print(f"✅ System status retrieved: {status.get('integration_version', 'unknown')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Integration test failed (expected): {e}")
        print("   This is likely due to missing V2 orchestrator components")
        return False  # Expected to fail until we have full V2 implementation

def main():
    """Run all tests"""
    print("🧪 V2-Only System Minimal Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Environment setup
    results.append(test_environment_setup())
    
    # Test 2: Module imports
    results.append(test_imports())
    
    # Test 3: Integration import (expected to fail)
    results.append(test_orchestrator_integration_import())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    print(f"📊 Success Rate: {passed/total*100:.1f}%")
    
    if passed >= 2:  # Environment + imports should work
        print("\n🎉 CORE SYSTEM READY!")
        print("Environment and dependencies are properly configured")
        if passed == 3:
            print("V2 orchestrator integration also working!")
        else:
            print("V2 orchestrator integration needs implementation")
    else:
        print(f"\n⚠️ {total-passed} critical tests failed")
        print("System setup incomplete")
    
    return passed >= 2  # Core functionality ready

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)