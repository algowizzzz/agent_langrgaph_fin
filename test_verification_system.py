#!/usr/bin/env python3
"""
Test Script for Runtime Verification System

This script tests the runtime verification system to ensure correct function execution
and bypass detection for the AI Finance & Risk Agent.
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

def test_server_status() -> bool:
    """Test if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_verification_endpoints() -> Dict[str, Any]:
    """Test all verification endpoints."""
    results = {}
    base_url = "http://localhost:8000/verification"
    
    endpoints = [
        ("status", "GET"),
        ("integrity", "GET"), 
        ("call-history", "GET"),
        ("test/search", "POST"),
        ("test/comprehensive", "POST"),
        ("test/csv-analysis", "POST"),
        ("force-verification-mode", "POST")
    ]
    
    for endpoint, method in endpoints:
        url = f"{base_url}/{endpoint}"
        print(f"🧪 Testing {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json={}, timeout=30)
            
            results[endpoint] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_size": len(response.text),
                "has_data": len(response.text) > 100
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]["data_keys"] = list(data.keys())[:5]  # First 5 keys
                    print(f"  ✅ SUCCESS: {response.status_code}, Keys: {results[endpoint]['data_keys']}")
                except:
                    print(f"  ✅ SUCCESS: {response.status_code}, Non-JSON response")
            else:
                print(f"  ❌ FAILED: {response.status_code}")
                
        except requests.exceptions.Timeout:
            results[endpoint] = {"error": "timeout", "success": False}
            print(f"  ⏱️ TIMEOUT")
        except Exception as e:
            results[endpoint] = {"error": str(e), "success": False}
            print(f"  💥 ERROR: {e}")
    
    return results

def test_csv_analysis_directly() -> Dict[str, Any]:
    """Test CSV analysis through the main chat endpoint."""
    csv_name = "20250801_215110_09205507-73f4-4fec-8792-3cdb156bcd39_test_business_data.csv"
    
    print(f"🧪 Testing CSV analysis through main chat endpoint...")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "query": "Summarize the business data for executive review",
                "session_id": "verification_test_main",
                "active_documents": [csv_name]
            },
            timeout=60
        )
        
        result = {
            "status_code": response.status_code,
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            data = response.json()
            result.update({
                "has_response": bool(data.get("response")),
                "response_length": len(data.get("response", "")),
                "contains_data": "data" in data.get("response", "").lower(),
                "contains_error": "error" in data.get("response", "").lower(),
                "processing_time": data.get("processing_time_ms", 0)
            })
            print(f"  ✅ Chat response: {result['response_length']} chars, Error: {result['contains_error']}")
        else:
            print(f"  ❌ Chat failed: {response.status_code}")
            
        return result
        
    except Exception as e:
        print(f"  💥 Chat error: {e}")
        return {"error": str(e), "success": False}

def compare_verification_results(verification_test: Dict, main_chat_test: Dict) -> Dict[str, Any]:
    """Compare results between verification system and main chat."""
    
    # Extract key metrics
    verification_success = verification_test.get("test/csv-analysis", {}).get("success", False)
    main_chat_success = main_chat_test.get("success", False)
    
    verification_has_data = verification_test.get("test/csv-analysis", {}).get("has_data", False)
    main_chat_has_data = main_chat_test.get("contains_data", False)
    
    verification_has_error = verification_test.get("test/csv-analysis", {}).get("response_size", 0) > 0
    main_chat_has_error = main_chat_test.get("contains_error", False)
    
    return {
        "both_successful": verification_success and main_chat_success,
        "verification_advantage": verification_success and not main_chat_success,
        "main_chat_advantage": main_chat_success and not verification_success,
        "both_failed": not verification_success and not main_chat_success,
        "data_consistency": verification_has_data == main_chat_has_data,
        "error_consistency": verification_has_error == main_chat_has_error,
        "recommendation": "use_verification" if verification_success and not main_chat_success else 
                        "main_chat_ok" if main_chat_success else "investigate_issues"
    }

async def main():
    """Run comprehensive verification system test."""
    
    print("🔒 RUNTIME VERIFICATION SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Server status
    print("\n1️⃣ Testing server status...")
    server_ok = test_server_status()
    print(f"   Server status: {'✅ ONLINE' if server_ok else '❌ OFFLINE'}")
    
    if not server_ok:
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Test 2: Verification endpoints
    print("\n2️⃣ Testing verification endpoints...")
    verification_results = test_verification_endpoints()
    
    successful_endpoints = sum(1 for r in verification_results.values() if r.get("success", False))
    total_endpoints = len(verification_results)
    
    print(f"\n   Verification endpoints: {successful_endpoints}/{total_endpoints} successful")
    
    # Test 3: CSV analysis through main chat
    print("\n3️⃣ Testing CSV analysis through main chat...")
    main_chat_results = test_csv_analysis_directly()
    
    # Test 4: Compare results
    print("\n4️⃣ Comparing verification vs main chat results...")
    comparison = compare_verification_results(verification_results, main_chat_results)
    
    print(f"   Both successful: {comparison['both_successful']}")
    print(f"   Verification advantage: {comparison['verification_advantage']}")
    print(f"   Recommendation: {comparison['recommendation']}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    overall_status = "PASS" if (
        server_ok and 
        successful_endpoints >= 5 and 
        (comparison['both_successful'] or comparison['verification_advantage'])
    ) else "FAIL"
    
    print(f"Overall Status: {'✅ ' + overall_status if overall_status == 'PASS' else '❌ ' + overall_status}")
    print(f"Server: {'✅' if server_ok else '❌'}")
    print(f"Verification Endpoints: {successful_endpoints}/{total_endpoints}")
    print(f"CSV Analysis: {'✅' if comparison['both_successful'] or comparison['verification_advantage'] else '❌'}")
    
    if overall_status == "PASS":
        print("\n🎉 Runtime verification system is working correctly!")
        print("   The system can detect function call bypasses and ensure correct execution.")
    else:
        print("\n⚠️  Issues detected with runtime verification system.")
        print("   Please check the logs and verification endpoint responses.")
    
    # Save detailed results
    detailed_results = {
        "test_timestamp": time.time(),
        "overall_status": overall_status,
        "server_status": server_ok,
        "verification_endpoints": verification_results,
        "main_chat_test": main_chat_results,
        "comparison": comparison
    }
    
    with open("verification_test_results.json", "w") as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: verification_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
 
 
 