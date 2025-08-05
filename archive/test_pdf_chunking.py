#!/usr/bin/env python3

"""
PDF Context-Aware Chunking Test
===============================

This script tests context-aware chunking specifically on PDF files,
showing detailed results and analysis.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# PDF processing
try:
    import PyPDF2
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False
    print("⚠️  PyPDF2 not available. PDF processing disabled.")

# Try to import the existing ContextAwareChunker
try:
    from test_context_aware_chunking import ContextAwareChunker
    HAS_CHUNKER = True
except ImportError:
    HAS_CHUNKER = False

class PDFChunkingAnalyzer:
    """Analyze PDF chunking results in detail."""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if HAS_CHUNKER:
            self.chunker = ContextAwareChunker(chunk_size, chunk_overlap)
        else:
            print("⚠️  ContextAwareChunker not available. Using basic analysis.")
            self.chunker = None
    
    def extract_pdf_text(self, pdf_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text from PDF file with metadata."""
        if not HAS_PDF_SUPPORT:
            raise Exception("PyPDF2 not available for PDF processing")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise Exception(f"PDF file not found: {pdf_path}")
        
        text_content = []
        page_info = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"📄 Processing PDF: {pdf_path.name}")
            print(f"📊 Total pages: {total_pages}")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        # Enhanced page formatting for better structure detection
                        formatted_page = f"\n\n## Page {page_num + 1}\n\n{page_text}"
                        text_content.append(formatted_page)
                        page_info.append({
                            'page_num': page_num + 1,
                            'char_count': len(page_text),
                            'word_count': len(page_text.split()),
                            'has_content': True
                        })
                        print(f"  ✅ Page {page_num + 1}: {len(page_text)} characters")
                    else:
                        page_info.append({
                            'page_num': page_num + 1,
                            'char_count': 0,
                            'word_count': 0,
                            'has_content': False
                        })
                        print(f"  ⚪ Page {page_num + 1}: Empty")
                except Exception as e:
                    print(f"  ❌ Page {page_num + 1}: Error - {str(e)}")
                    page_info.append({
                        'page_num': page_num + 1,
                        'char_count': 0,
                        'word_count': 0,
                        'has_content': False,
                        'error': str(e)
                    })
        
        full_text = "\n".join(text_content)
        
        metadata = {
            'source': str(pdf_path),
            'file_type': 'PDF',
            'file_name': pdf_path.name,
            'total_pages': total_pages,
            'total_characters': len(full_text),
            'total_words': len(full_text.split()),
            'pages_with_content': sum(1 for p in page_info if p['has_content']),
            'page_details': page_info
        }
        
        return full_text, metadata
    
    def analyze_chunking(self, pdf_path: str) -> Dict[str, Any]:
        """Perform comprehensive chunking analysis on PDF."""
        print("\n🔍 DETAILED PDF CHUNKING ANALYSIS")
        print("=" * 60)
        
        # Extract PDF text
        try:
            content, pdf_metadata = self.extract_pdf_text(pdf_path)
            
            print(f"\n📊 PDF Statistics:")
            print(f"  File: {pdf_metadata['file_name']}")
            print(f"  Pages: {pdf_metadata['total_pages']}")
            print(f"  Pages with content: {pdf_metadata['pages_with_content']}")
            print(f"  Total characters: {pdf_metadata['total_characters']:,}")
            print(f"  Total words: {pdf_metadata['total_words']:,}")
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            return {'error': str(e)}
        
        if not content.strip():
            print("❌ No text content extracted from PDF")
            return {'error': 'No text content found'}
        
        # Perform chunking analysis
        if self.chunker:
            print(f"\n🧩 Chunking Analysis:")
            
            # Test structure detection
            has_structure = self.chunker._detect_structure(content)
            print(f"  Structure detected: {'✅ Yes' if has_structure else '❌ No'}")
            
            # Perform chunking
            chunk_result = self.chunker.chunk_text(content, pdf_metadata)
            
            print(f"  Method used: {chunk_result.method_used}")
            print(f"  Total chunks: {chunk_result.total_chunks}")
            print(f"  Average chunk size: {chunk_result.avg_chunk_size:.1f} characters")
            
            # Analyze chunks in detail
            self._analyze_chunks_detail(chunk_result.chunks)
            
            # Show page distribution
            self._analyze_page_distribution(chunk_result.chunks, pdf_metadata)
            
            return {
                'pdf_metadata': pdf_metadata,
                'chunking_method': chunk_result.method_used,
                'total_chunks': chunk_result.total_chunks,
                'avg_chunk_size': chunk_result.avg_chunk_size,
                'chunks': chunk_result.chunks,
                'has_structure': has_structure
            }
        else:
            print("⚠️  Advanced chunking not available")
            return {'error': 'Chunker not available'}
    
    def _analyze_chunks_detail(self, chunks: List[Dict[str, Any]]):
        """Analyze chunks in detail."""
        print(f"\n📋 Chunk Details:")
        
        # Size distribution
        sizes = [chunk['size'] for chunk in chunks]
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0
        
        print(f"  Size range: {min_size} - {max_size} characters")
        
        # Show first few chunks
        print(f"\n📝 First 5 Chunks:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n  Chunk {i+1}:")
            print(f"    Size: {chunk['size']} characters")
            
            # Show metadata
            metadata = chunk['metadata']
            if any(key.startswith('Header') for key in metadata.keys()):
                headers = {k: v for k, v in metadata.items() if k.startswith('Header')}
                print(f"    Headers: {headers}")
            
            # Show content preview
            content_preview = chunk['content'][:200].replace('\n', ' ')
            print(f"    Content: {content_preview}...")
            
            # Check if this chunk mentions specific pages
            page_mentions = re.findall(r'## Page (\d+)', chunk['content'])
            if page_mentions:
                print(f"    Contains pages: {', '.join(page_mentions)}")
    
    def _analyze_page_distribution(self, chunks: List[Dict[str, Any]], pdf_metadata: Dict[str, Any]):
        """Analyze how pages are distributed across chunks."""
        print(f"\n🗂️  Page Distribution Analysis:")
        
        page_to_chunks = {}
        
        for i, chunk in enumerate(chunks):
            # Find page mentions in chunk content
            page_mentions = re.findall(r'## Page (\d+)', chunk['content'])
            for page_str in page_mentions:
                page_num = int(page_str)
                if page_num not in page_to_chunks:
                    page_to_chunks[page_num] = []
                page_to_chunks[page_num].append(i + 1)
        
        if page_to_chunks:
            print(f"  Pages found in chunks:")
            for page_num in sorted(page_to_chunks.keys()):
                chunk_list = page_to_chunks[page_num]
                print(f"    Page {page_num}: Chunks {', '.join(map(str, chunk_list))}")
        else:
            print(f"  No clear page markers found in chunks")
        
        # Check for cross-page chunks
        cross_page_chunks = 0
        for chunk in chunks:
            page_mentions = re.findall(r'## Page (\d+)', chunk['content'])
            if len(page_mentions) > 1:
                cross_page_chunks += 1
        
        if cross_page_chunks > 0:
            print(f"  Cross-page chunks: {cross_page_chunks} (chunks spanning multiple pages)")
        
        # Calculate chunks per page average
        total_pages = pdf_metadata.get('pages_with_content', 0)
        if total_pages > 0:
            chunks_per_page = len(chunks) / total_pages
            print(f"  Average chunks per page: {chunks_per_page:.1f}")

def main():
    """Main function to run PDF chunking analysis."""
    pdf_file = "car24_chpt1_0.pdf"
    
    print("🚀 PDF Context-Aware Chunking Analysis")
    print("=" * 50)
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file not found: {pdf_file}")
        print("📁 Available PDF files:")
        for pdf in Path(".").glob("*.pdf"):
            print(f"  - {pdf.name}")
        return
    
    if not HAS_PDF_SUPPORT:
        print("❌ PyPDF2 not available. Please install: pip install PyPDF2")
        return
    
    # Create analyzer
    analyzer = PDFChunkingAnalyzer(chunk_size=1500, chunk_overlap=200)
    
    # Run analysis
    results = analyzer.analyze_chunking(pdf_file)
    
    if 'error' not in results:
        print("\n🎉 Analysis completed successfully!")
        print(f"\n📈 Summary:")
        print(f"  PDF: {results['pdf_metadata']['file_name']}")
        print(f"  Method: {results['chunking_method']}")
        print(f"  Chunks: {results['total_chunks']}")
        print(f"  Avg size: {results['avg_chunk_size']:.1f} chars")
        print(f"  Structure detected: {'✅' if results['has_structure'] else '❌'}")
    else:
        print(f"❌ Analysis failed: {results['error']}")

if __name__ == "__main__":
    main()