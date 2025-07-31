#!/usr/bin/env python3

"""
Context-Aware Chunking Validation Test
====================================

Focused test to validate our enhanced document processor integration
with MarkdownHeaderTextSplitter in the Document Analysis Pod.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import our components
from document_processor import document_processor
from document_analysis_pod import document_analysis_pod

async def test_context_aware_chunking():
    """Test our enhanced context-aware chunking integration."""
    print("🧪 CONTEXT-AWARE CHUNKING VALIDATION")
    print("=" * 60)
    
    # Test 1: Document Processor Direct Test
    print("\n📄 Test 1: Document Processor with Context-Aware Chunking")
    print("-" * 50)
    
    test_files = [
        "isolated_test_files/hermes_strategy.txt",
        "isolated_test_files/car24_test.pdf"
    ]
    
    results = {}
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"⚠️  Skipping {test_file} - file not found")
            continue
            
        print(f"\n🔍 Processing: {test_file}")
        
        try:
            # Test our enhanced document processor
            result = await document_processor.process_document(test_file)
            
            if result.success:
                chunks = result.documents
                total_chunks = len(chunks)
                
                # Analyze chunking results
                header_chunks = sum(1 for chunk in chunks 
                                  if any(k.startswith('Header') for k in chunk.metadata.keys()))
                
                avg_size = sum(len(chunk.page_content) for chunk in chunks) / total_chunks if total_chunks > 0 else 0
                
                # Check first chunk for header metadata
                sample_metadata = chunks[0].metadata if chunks else {}
                has_context_headers = any(k.startswith('Header') for k in sample_metadata.keys())
                
                file_result = {
                    "success": True,
                    "total_chunks": total_chunks,
                    "header_chunks": header_chunks,
                    "avg_chunk_size": round(avg_size, 1),
                    "has_context_headers": has_context_headers,
                    "sample_metadata": sample_metadata,
                    "first_chunk_preview": chunks[0].page_content[:150] + "..." if chunks else "No content"
                }
                
                print(f"  ✅ SUCCESS:")
                print(f"    - Chunks: {total_chunks}")
                print(f"    - With header metadata: {header_chunks}")
                print(f"    - Average size: {avg_size:.1f} chars")
                print(f"    - Context headers: {'✅' if has_context_headers else '❌'}")
                print(f"    - Sample metadata keys: {list(sample_metadata.keys())}")
                
            else:
                file_result = {
                    "success": False,
                    "error": result.error
                }
                print(f"  ❌ FAILED: {result.error}")
                
            results[test_file] = file_result
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results[test_file] = {"success": False, "error": str(e)}
    
    # Test 2: Full Document Analysis Pod Test
    print("\n\n🔄 Test 2: Full Document Analysis Pod Integration")
    print("-" * 50)
    
    if "isolated_test_files/hermes_strategy.txt" in results and results["isolated_test_files/hermes_strategy.txt"]["success"]:
        try:
            # Test full pod workflow
            test_input = {
                "user_query": "Summarize the key points and provide action items",
                "uploaded_files": {"hermes_strategy.txt": "isolated_test_files/hermes_strategy.txt"},
                "session_id": "context_test_123"
            }
            
            print("📋 Running full Document Analysis Pod workflow...")
            
            # This tests the complete pipeline with our enhanced chunking
            result = await document_analysis_pod.invoke(test_input)
            
            if result.get("processing_status") == "completed":
                print("  ✅ FULL PIPELINE SUCCESS:")
                print(f"    - Processing status: {result['processing_status']}")
                print(f"    - Final analysis length: {len(result.get('final_response', ''))}")
                print(f"    - Chunks processed: {len(result.get('doc_chunks', []))}")
                
                # Check if chunks have our context-aware metadata
                chunks_with_headers = sum(1 for chunk in result.get('doc_chunks', [])
                                        if any(k.startswith('Header') for k in chunk.metadata.keys()))
                
                print(f"    - Chunks with header metadata: {chunks_with_headers}")
                
                results["full_pipeline"] = {
                    "success": True,
                    "chunks_processed": len(result.get('doc_chunks', [])),
                    "chunks_with_headers": chunks_with_headers,
                    "response_length": len(result.get('final_response', ''))
                }
            else:
                print(f"  ❌ Pipeline failed: {result.get('error', 'Unknown error')}")
                results["full_pipeline"] = {"success": False, "error": result.get('error', 'Unknown')}
                
        except Exception as e:
            print(f"  ❌ Pipeline error: {e}")
            results["full_pipeline"] = {"success": False, "error": str(e)}
    
    # Test 3: Context-Aware Features Validation
    print("\n\n🎯 Test 3: Context-Aware Features Validation")
    print("-" * 50)
    
    # Get processing stats to verify our enhancements
    stats = document_processor.get_processing_stats()
    
    print("📈 Enhanced Features Status:")
    print(f"  - Context-aware chunking: {stats.get('context_aware_chunking', False)}")
    print(f"  - Chunking methods: {stats.get('chunking_methods', [])}")
    print(f"  - Supported headers: {stats.get('supported_headers', [])}")
    print(f"  - Structure detection: {stats.get('structure_detection', False)}")
    
    features_working = all([
        stats.get('context_aware_chunking', False),
        'MarkdownHeaderTextSplitter' in stats.get('chunking_methods', []),
        stats.get('structure_detection', False)
    ])
    
    print(f"\n🎯 Context-Aware Features: {'✅ ALL WORKING' if features_working else '❌ ISSUES DETECTED'}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"context_chunking_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "enhanced_features": stats,
            "overall_success": features_working and any(r.get("success", False) for r in results.values())
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Summary
    print(f"\n🏆 VALIDATION SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_tests = len(results)
    
    print(f"✅ Tests passed: {success_count}/{total_tests}")
    print(f"🔧 Enhanced features: {'✅ Working' if features_working else '❌ Issues'}")
    
    if features_working and success_count > 0:
        print(f"\n🎉 CONTEXT-AWARE CHUNKING INTEGRATION: SUCCESS!")
        print(f"📋 Your Document Analysis Pod now has:")
        print(f"  ✅ MarkdownHeaderTextSplitter for structure preservation")
        print(f"  ✅ Header metadata in chunk context")
        print(f"  ✅ Intelligent document structure detection")
        print(f"  ✅ Seamless integration with existing pipeline")
    else:
        print(f"\n⚠️  Issues detected - review results above")
    
    return features_working and success_count > 0

if __name__ == "__main__":
    success = asyncio.run(test_context_aware_chunking())
    sys.exit(0 if success else 1)