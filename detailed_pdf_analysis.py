#!/usr/bin/env python3

"""
Detailed PDF Chunking Results Viewer
===================================

Shows comprehensive chunking results with content samples and structure analysis.
"""

import sys
import os
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_pdf_chunking import PDFChunkingAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False

def show_detailed_chunks(pdf_path: str, max_chunks_to_show: int = 10):
    """Show detailed chunk analysis with content samples."""
    if not HAS_ANALYZER:
        print("❌ PDF analyzer not available")
        return
    
    print("🔍 DETAILED CHUNK CONTENT ANALYSIS")
    print("=" * 70)
    
    analyzer = PDFChunkingAnalyzer(chunk_size=1500, chunk_overlap=200)
    results = analyzer.analyze_chunking(pdf_path)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    chunks = results['chunks']
    
    # Show document structure overview
    print(f"\n📚 DOCUMENT STRUCTURE OVERVIEW")
    print("-" * 50)
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunking method: {results['chunking_method']}")
    print(f"Document has structure: {results['has_structure']}")
    
    # Analyze header hierarchy
    header_levels = {}
    for chunk in chunks:
        for key, value in chunk['metadata'].items():
            if key.startswith('Header'):
                if key not in header_levels:
                    header_levels[key] = set()
                header_levels[key].add(value)
    
    if header_levels:
        print(f"\n🏷️  HEADER HIERARCHY DETECTED:")
        for level in sorted(header_levels.keys()):
            headers = list(header_levels[level])[:5]  # Show first 5
            print(f"  {level}: {len(header_levels[level])} unique headers")
            for header in headers:
                print(f"    - {header}")
            if len(header_levels[level]) > 5:
                print(f"    ... and {len(header_levels[level]) - 5} more")
    
    # Show chunk size distribution
    sizes = [chunk['size'] for chunk in chunks]
    size_ranges = {
        'Small (< 500)': len([s for s in sizes if s < 500]),
        'Medium (500-1000)': len([s for s in sizes if 500 <= s < 1000]),
        'Large (1000-1500)': len([s for s in sizes if 1000 <= s <= 1500]),
        'Oversized (> 1500)': len([s for s in sizes if s > 1500])
    }
    
    print(f"\n📊 CHUNK SIZE DISTRIBUTION:")
    for range_name, count in size_ranges.items():
        percentage = (count / len(chunks)) * 100 if chunks else 0
        print(f"  {range_name}: {count} chunks ({percentage:.1f}%)")
    
    # Show detailed content for first N chunks
    print(f"\n📝 DETAILED CHUNK CONTENTS (First {max_chunks_to_show} chunks):")
    print("=" * 70)
    
    for i, chunk in enumerate(chunks[:max_chunks_to_show]):
        print(f"\n🔸 CHUNK {i+1}")
        print("-" * 40)
        print(f"Size: {chunk['size']} characters")
        
        # Show metadata
        metadata = chunk['metadata']
        print(f"Metadata:")
        for key, value in metadata.items():
            if key.startswith('Header'):
                print(f"  {key}: {value}")
            elif key in ['source', 'file_type', 'file_name']:
                print(f"  {key}: {value}")
        
        # Show content with formatting
        content = chunk['content']
        
        # Identify content type
        if '## Page' in content:
            page_match = content.split('## Page')[1].split('\n')[0].strip()
            print(f"📄 Contains: Page {page_match}")
        
        # Show first few lines
        lines = content.split('\n')
        preview_lines = []
        char_count = 0
        
        for line in lines[:10]:  # Show up to 10 lines
            if char_count + len(line) > 300:  # Limit to ~300 chars
                break
            preview_lines.append(line)
            char_count += len(line)
        
        print(f"Content preview:")
        for line in preview_lines:
            if line.strip():
                print(f"  {line}")
        
        if len(content) > 300:
            print(f"  ... [+{len(content) - 300} more characters]")
        
        # Check for specific document elements
        elements = []
        if 'Table of Contents' in content:
            elements.append('📋 Table of Contents')
        if any(word in content.lower() for word in ['chapter', 'section']):
            elements.append('📖 Chapter/Section')
        if any(char in content for char in ['•', '-', '1.', '2.']):
            elements.append('📝 Lists/Bullets')
        if any(word in content.lower() for word in ['table', 'figure', 'chart']):
            elements.append('📊 Tables/Figures')
        
        if elements:
            print(f"Document elements: {', '.join(elements)}")
    
    # Show page-to-chunk mapping in detail
    print(f"\n🗂️  PAGE-TO-CHUNK MAPPING:")
    print("-" * 40)
    
    page_chunks = {}
    for i, chunk in enumerate(chunks):
        content = chunk['content']
        if '## Page' in content:
            try:
                page_num = int(content.split('## Page')[1].split('\n')[0].strip())
                if page_num not in page_chunks:
                    page_chunks[page_num] = []
                page_chunks[page_num].append({
                    'chunk_id': i + 1,
                    'size': chunk['size'],
                    'has_headers': any(k.startswith('Header') for k in chunk['metadata'].keys())
                })
            except:
                pass
    
    for page_num in sorted(page_chunks.keys())[:10]:  # Show first 10 pages
        chunks_info = page_chunks[page_num]
        print(f"Page {page_num}:")
        for chunk_info in chunks_info:
            headers_indicator = "🏷️" if chunk_info['has_headers'] else "📄"
            print(f"  {headers_indicator} Chunk {chunk_info['chunk_id']} ({chunk_info['size']} chars)")
    
    if len(page_chunks) > 10:
        print(f"  ... and {len(page_chunks) - 10} more pages")
    
    # Summary statistics
    print(f"\n📈 CHUNKING EFFECTIVENESS SUMMARY:")
    print("-" * 50)
    total_chars = sum(chunk['size'] for chunk in chunks)
    avg_size = total_chars / len(chunks) if chunks else 0
    
    print(f"✅ Successfully processed: {results['pdf_metadata']['pages_with_content']} pages")
    print(f"📊 Created: {len(chunks)} chunks")
    print(f"📏 Average chunk size: {avg_size:.0f} characters")
    print(f"🎯 Method used: {results['chunking_method']}")
    print(f"🏗️  Structure preserved: {'Yes' if results['has_structure'] else 'No'}")
    
    # Calculate efficiency metrics
    chunks_with_headers = sum(1 for chunk in chunks if any(k.startswith('Header') for k in chunk['metadata'].keys()))
    if chunks_with_headers > 0:
        print(f"🏷️  Chunks with header metadata: {chunks_with_headers} ({(chunks_with_headers/len(chunks)*100):.1f}%)")
    
    # Overlap analysis
    if results['chunking_method'] == 'context_aware':
        print(f"🔗 Context preservation: Excellent (header-based splitting)")
    else:
        print(f"🔗 Context preservation: Good (recursive splitting)")

def save_chunking_results(pdf_path: str, output_file: str = None):
    """Save chunking results to JSON file for further analysis."""
    if not HAS_ANALYZER:
        print("❌ PDF analyzer not available")
        return
    
    analyzer = PDFChunkingAnalyzer(chunk_size=1500, chunk_overlap=200)
    results = analyzer.analyze_chunking(pdf_path)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    if output_file is None:
        pdf_name = Path(pdf_path).stem
        output_file = f"{pdf_name}_chunking_results.json"
    
    # Prepare data for JSON serialization
    json_data = {
        'pdf_file': pdf_path,
        'analysis_date': str(Path(pdf_path).stat().st_mtime),
        'chunking_method': results['chunking_method'],
        'total_chunks': results['total_chunks'],
        'avg_chunk_size': results['avg_chunk_size'],
        'has_structure': results['has_structure'],
        'pdf_stats': {
            'total_pages': results['pdf_metadata']['total_pages'],
            'pages_with_content': results['pdf_metadata']['pages_with_content'],
            'total_characters': results['pdf_metadata']['total_characters'],
            'total_words': results['pdf_metadata']['total_words']
        },
        'chunks': [
            {
                'chunk_id': i + 1,
                'size': chunk['size'],
                'content_preview': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                'metadata': chunk['metadata']
            }
            for i, chunk in enumerate(results['chunks'])
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Chunking results saved to: {output_file}")
    return output_file

def main():
    """Main function."""
    pdf_file = "car24_chpt1_0.pdf"
    
    print("🔍 COMPREHENSIVE PDF CHUNKING ANALYSIS")
    print("=" * 60)
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    # Show detailed analysis
    show_detailed_chunks(pdf_file, max_chunks_to_show=15)
    
    # Save results
    print(f"\n💾 SAVING RESULTS:")
    print("-" * 30)
    output_file = save_chunking_results(pdf_file)
    
    if output_file:
        print(f"📄 Results saved to: {output_file}")
        print(f"📊 You can now examine the JSON file for complete chunk data")

if __name__ == "__main__":
    main()