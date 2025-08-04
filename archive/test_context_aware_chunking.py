#!/usr/bin/env python3

"""
Context-Aware Chunking Test Script
==================================

This script demonstrates and tests context-aware document chunking that preserves
document structure and hierarchy for better AI understanding.
"""

import asyncio
import tempfile
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class ChunkResult:
    """Result of chunking operation."""
    chunks: List[Dict[str, Any]]
    method_used: str
    total_chunks: int
    avg_chunk_size: float

class ContextAwareChunker:
    """Enhanced chunker that preserves document structure."""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Test if MarkdownHeaderTextSplitter is available
        self.has_markdown_splitter = self._test_markdown_splitter()
        
        if self.has_markdown_splitter:
            from langchain_text_splitters import MarkdownHeaderTextSplitter
            
            self.headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"), 
                ("###", "Header 3"),
                ("####", "Header 4"),
                ("#####", "Header 5"),
                ("######", "Header 6"),
            ]
            
            self.markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=self.headers_to_split_on,
                strip_headers=False  # Keep headers for context
            )
        
        # Fallback recursive splitter
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self.recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            self.has_recursive_splitter = True
        except ImportError:
            self.has_recursive_splitter = False
            print("⚠️  LangChain not available, using basic chunking")
    
    def _test_markdown_splitter(self) -> bool:
        """Test if MarkdownHeaderTextSplitter is available."""
        try:
            from langchain_text_splitters import MarkdownHeaderTextSplitter
            return True
        except ImportError:
            return False
    
    def chunk_text(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ChunkResult:
        """Chunk text using the best available method."""
        if metadata is None:
            metadata = {}
        
        # Detect if content has structure
        has_structure = self._detect_structure(content)
        
        if has_structure and self.has_markdown_splitter:
            return self._context_aware_chunk(content, metadata)
        elif self.has_recursive_splitter:
            return self._recursive_chunk(content, metadata)
        else:
            return self._basic_chunk(content, metadata)
    
    def _detect_structure(self, content: str) -> bool:
        """Detect if content has markdown-like structure."""
        # Look for markdown headers
        header_patterns = [
            r'^#{1,6}\s+.+$',  # Standard markdown headers
            r'^.+\n[=-]+\n',   # Underlined headers
        ]
        
        for pattern in header_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        # Additional structure indicators
        structure_indicators = [
            r'^\d+\.\s+',      # Numbered sections
            r'^[A-Z][^.]*:$',  # Title-like lines ending with colon
            r'^Chapter\s+\d+', # Chapter headers
            r'^Section\s+\d+', # Section headers
        ]
        
        structure_count = 0
        for pattern in structure_indicators:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                structure_count += 1
        
        return structure_count >= 2
    
    def _context_aware_chunk(self, content: str, metadata: Dict[str, Any]) -> ChunkResult:
        """Context-aware chunking using MarkdownHeaderTextSplitter."""
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        
        try:
            # Split by headers first
            header_splits = self.markdown_splitter.split_text(content)
            
            chunks = []
            for split in header_splits:
                # Extract content and metadata
                split_content = split.page_content if hasattr(split, 'page_content') else str(split)
                split_metadata = metadata.copy()
                
                if hasattr(split, 'metadata') and split.metadata:
                    split_metadata.update(split.metadata)
                
                # If chunk is still too large, apply secondary splitting
                if len(split_content) > self.chunk_size:
                    if self.has_recursive_splitter:
                        from langchain_core.documents import Document
                        sub_docs = self.recursive_splitter.create_documents(
                            [split_content], metadatas=[split_metadata]
                        )
                        for doc in sub_docs:
                            chunks.append({
                                'content': doc.page_content,
                                'metadata': doc.metadata,
                                'size': len(doc.page_content)
                            })
                    else:
                        # Basic splitting as fallback
                        sub_chunks = self._split_large_chunk(split_content, split_metadata)
                        chunks.extend(sub_chunks)
                else:
                    chunks.append({
                        'content': split_content,
                        'metadata': split_metadata,
                        'size': len(split_content)
                    })
            
            avg_size = sum(c['size'] for c in chunks) / len(chunks) if chunks else 0
            
            return ChunkResult(
                chunks=chunks,
                method_used="context_aware",
                total_chunks=len(chunks),
                avg_chunk_size=avg_size
            )
            
        except Exception as e:
            print(f"⚠️  Context-aware chunking failed: {e}")
            # Fallback to recursive chunking
            return self._recursive_chunk(content, metadata)
    
    def _recursive_chunk(self, content: str, metadata: Dict[str, Any]) -> ChunkResult:
        """Recursive chunking using LangChain's RecursiveCharacterTextSplitter."""
        try:
            from langchain_core.documents import Document
            
            documents = self.recursive_splitter.create_documents(
                [content], metadatas=[metadata]
            )
            
            chunks = []
            for doc in documents:
                chunks.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'size': len(doc.page_content)
                })
            
            avg_size = sum(c['size'] for c in chunks) / len(chunks) if chunks else 0
            
            return ChunkResult(
                chunks=chunks,
                method_used="recursive",
                total_chunks=len(chunks),
                avg_chunk_size=avg_size
            )
            
        except Exception as e:
            print(f"⚠️  Recursive chunking failed: {e}")
            return self._basic_chunk(content, metadata)
    
    def _basic_chunk(self, content: str, metadata: Dict[str, Any]) -> ChunkResult:
        """Basic chunking by splitting on sentences and paragraphs."""
        chunks = []
        
        # Split on double newlines first (paragraphs)
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk + paragraph) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': current_chunk.strip(),
                    'metadata': metadata,
                    'size': len(current_chunk.strip())
                })
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    # Take last part of current chunk as overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': metadata,
                'size': len(current_chunk.strip())
            })
        
        avg_size = sum(c['size'] for c in chunks) / len(chunks) if chunks else 0
        
        return ChunkResult(
            chunks=chunks,
            method_used="basic",
            total_chunks=len(chunks),
            avg_chunk_size=avg_size
        )
    
    def _split_large_chunk(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a large chunk into smaller pieces."""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            if end < len(content):
                # Try to find a good breaking point
                search_start = max(start + self.chunk_size - 100, start)
                search_end = min(end + 100, len(content))
                
                # Look for sentence endings
                break_points = []
                for i in range(search_start, search_end):
                    if content[i] in '.!?\n':
                        break_points.append(i + 1)
                
                if break_points:
                    # Use the break point closest to our target
                    target = start + self.chunk_size
                    end = min(break_points, key=lambda x: abs(x - target))
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    'content': chunk_content,
                    'metadata': metadata,
                    'size': len(chunk_content)
                })
            
            # Move start position with overlap
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end
        
        return chunks

def create_test_content():
    """Create test content with different structures."""
    
    structured_content = """# Document Analysis Report

This document provides a comprehensive analysis of business operations and strategic recommendations.

## Executive Summary

The executive summary highlights key findings and recommendations for stakeholders.

### Key Findings

Our analysis revealed three critical areas requiring immediate attention:

1. **Operational Efficiency**: Current processes show 15% inefficiency
2. **Market Position**: Competitive analysis indicates market share decline
3. **Technology Infrastructure**: Legacy systems require modernization

### Recommendations

Based on our findings, we recommend the following strategic initiatives:

## Chapter 1: Market Analysis

This chapter examines current market conditions and competitive landscape.

### Section 1.1: Market Overview

The market has experienced significant changes over the past year, with new entrants disrupting traditional models.

### Section 1.2: Competitive Analysis

Our main competitors have adopted aggressive pricing strategies and enhanced digital capabilities.

## Chapter 2: Operational Assessment

This chapter reviews internal operations and identifies improvement opportunities.

### Section 2.1: Process Efficiency

Current processes show bottlenecks in three key areas that impact customer satisfaction.

### Section 2.2: Resource Utilization

Human and technological resources are underutilized, presenting optimization opportunities.

## Conclusion

The analysis demonstrates clear opportunities for improvement across multiple dimensions.
"""

    unstructured_content = """This is a plain text document without any clear structural markers or headers. It contains various paragraphs discussing different business topics but lacks the organizational elements that would help with context-aware chunking. The content flows from one topic to another without clear demarcation or hierarchical structure.

The document discusses market conditions and operational challenges facing the organization. Various factors contribute to the current situation including competitive pressures, technological changes, and evolving customer expectations. These factors interact in complex ways that require careful analysis and strategic planning.

Current operational processes have evolved over time but may not be optimized for current market conditions. Legacy systems and procedures may create inefficiencies that impact overall performance. Staff training and development programs may need updates to address new challenges and opportunities.

Financial performance has been impacted by various external and internal factors. Revenue growth has slowed while costs have increased in several categories. Profit margins have declined compared to previous periods. Investment in new technologies and capabilities requires careful planning and resource allocation.

Customer satisfaction metrics indicate areas for improvement in service delivery and product quality. Feedback mechanisms need enhancement to better understand customer needs and expectations. Competitive analysis shows other organizations are implementing innovative approaches to customer engagement and retention."""

    return structured_content, unstructured_content

def print_chunk_analysis(result: ChunkResult, title: str):
    """Print detailed analysis of chunking results."""
    print(f"\n📊 {title}")
    print("-" * 50)
    print(f"Method Used: {result.method_used}")
    print(f"Total Chunks: {result.total_chunks}")
    print(f"Average Chunk Size: {result.avg_chunk_size:.1f} characters")
    
    if result.chunks:
        print(f"\nFirst 3 chunks:")
        for i, chunk in enumerate(result.chunks[:3]):
            print(f"\n  Chunk {i+1}:")
            print(f"    Size: {chunk['size']} characters")
            print(f"    Content preview: {chunk['content'][:100]}...")
            if chunk['metadata']:
                print(f"    Metadata: {chunk['metadata']}")

async def run_comprehensive_test():
    """Run comprehensive test of context-aware chunking."""
    print("🚀 Context-Aware Chunking Test Suite")
    print("=" * 60)
    
    # Test 1: Check dependencies
    print("\n🔧 Test 1: Dependency Check")
    print("-" * 30)
    
    chunker = ContextAwareChunker()
    
    print(f"MarkdownHeaderTextSplitter available: {'✅' if chunker.has_markdown_splitter else '❌'}")
    print(f"RecursiveCharacterTextSplitter available: {'✅' if chunker.has_recursive_splitter else '❌'}")
    
    # Test 2: Structure Detection
    print("\n🔍 Test 2: Structure Detection")
    print("-" * 30)
    
    structured_content, unstructured_content = create_test_content()
    
    structured_detected = chunker._detect_structure(structured_content)
    unstructured_detected = chunker._detect_structure(unstructured_content)
    
    print(f"Structured content detected: {'✅' if structured_detected else '❌'}")
    print(f"Unstructured content correctly identified: {'✅' if not unstructured_detected else '❌'}")
    
    # Test 3: Chunking Comparison
    print("\n📄 Test 3: Chunking Comparison")
    print("-" * 30)
    
    # Test structured content
    structured_result = chunker.chunk_text(
        structured_content, 
        {"source": "test_structured.md", "file_type": "markdown"}
    )
    
    print_chunk_analysis(structured_result, "Structured Content Results")
    
    # Test unstructured content
    unstructured_result = chunker.chunk_text(
        unstructured_content,
        {"source": "test_unstructured.txt", "file_type": "text"}
    )
    
    print_chunk_analysis(unstructured_result, "Unstructured Content Results")
    
    # Test 4: Real File Processing (if available)
    print("\n📁 Test 4: Real File Processing")
    print("-" * 30)
    
    test_files = [
        "test_small.txt",
        "business_testing/isolated_test_files/hermes_strategy.txt",
        "README.md"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n🔍 Processing: {test_file}")
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                result = chunker.chunk_text(
                    content,
                    {"source": test_file, "file_type": Path(test_file).suffix}
                )
                
                print(f"  ✅ Success: {result.total_chunks} chunks using {result.method_used} method")
                print(f"  📏 Average size: {result.avg_chunk_size:.1f} characters")
                
                # Show metadata from first chunk if it has header context
                if result.chunks and any(key.startswith('Header') for key in result.chunks[0]['metadata'].keys()):
                    print(f"  🏷️  Contains header metadata: ✅")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"📝 File not found: {test_file}")
    
    # Test 5: Performance Comparison
    print("\n⚡ Test 5: Performance Summary")
    print("-" * 30)
    
    print(f"Structured content:")
    print(f"  - Method: {structured_result.method_used}")
    print(f"  - Chunks: {structured_result.total_chunks}")
    print(f"  - Avg size: {structured_result.avg_chunk_size:.1f}")
    
    print(f"\nUnstructured content:")
    print(f"  - Method: {unstructured_result.method_used}")
    print(f"  - Chunks: {unstructured_result.total_chunks}")
    print(f"  - Avg size: {unstructured_result.avg_chunk_size:.1f}")
    
    # Benefits analysis
    if structured_result.method_used == "context_aware":
        print(f"\n🎯 Context-Aware Benefits:")
        print(f"  - Preserves document hierarchy")
        print(f"  - Maintains semantic relationships")
        print(f"  - Provides header metadata for better AI understanding")
        print(f"  - Adaptive chunking based on content structure")

def create_sample_files():
    """Create sample files for testing."""
    print("\n📝 Creating Sample Test Files")
    print("-" * 30)
    
    structured_content, unstructured_content = create_test_content()
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(structured_content)
        structured_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(unstructured_content)
        unstructured_file = f.name
    
    print(f"✅ Created structured test file: {structured_file}")
    print(f"✅ Created unstructured test file: {unstructured_file}")
    
    return structured_file, unstructured_file

if __name__ == "__main__":
    print("🧪 Starting Context-Aware Chunking Tests")
    
    # Run the test suite
    asyncio.run(run_comprehensive_test())
    
    print("\n✨ Testing completed!")
    print("\n💡 Next Steps:")
    print("  1. Install missing dependencies if needed:")
    print("     pip install langchain-text-splitters langchain-core")
    print("  2. Integrate context-aware chunking into document_processor.py")
    print("  3. Test with your actual document processing workflow")