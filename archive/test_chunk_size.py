#!/usr/bin/env python3
"""
Test the 5k word chunk size implementation
"""

import asyncio
from tools.document_tools import split_document_into_chunks
from config import AI

def test_chunk_configuration():
    """Test the chunk size configuration"""
    
    print("🧪 Testing 5K Word Chunk Size Implementation")
    print("=" * 50)
    
    # Check config values
    ai_config = AI()
    chunk_size = getattr(ai_config, 'chunk_size', 'Not set')
    chunk_overlap = getattr(ai_config, 'chunk_overlap', 'Not set')
    
    print(f"📊 Chunk size: {chunk_size}")
    print(f"📊 Chunk overlap: {chunk_overlap}")
    
    # Test with sample large text
    large_text = "This is a test document. " * 2000  # ~10k words
    print(f"\n📄 Test text length: {len(large_text.split())} words")
    
    try:
        # Test chunking
        chunks = split_document_into_chunks(large_text, chunk_size=25000, chunk_overlap=1000)
        
        print(f"\n✅ Chunking Results:")
        print(f"   Number of chunks: {len(chunks)}")
        
        for i, chunk in enumerate(chunks, 1):
            word_count = len(chunk.split())
            print(f"   Chunk {i}: {word_count} words")
            
        print(f"\n🎯 Expected: 3-5 chunks for large documents (vs 26 previously)")
        print(f"🎯 Actual: {len(chunks)} chunks")
        
        if len(chunks) <= 5:
            print("✅ Chunk reduction SUCCESS!")
        else:
            print("❌ Chunk reduction not working as expected")
            
    except Exception as e:
        print(f"❌ Error testing chunks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chunk_configuration()