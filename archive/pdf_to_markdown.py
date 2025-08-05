#!/usr/bin/env python3
"""
Extract PDF content as structured markdown using PyMuPDF
"""

import fitz  # PyMuPDF
import sys
from pathlib import Path

def extract_pdf_as_markdown(pdf_path: str, output_path: str) -> bool:
    """Extract PDF content as markdown with proper structure."""
    
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        
        print(f"📄 Processing PDF: {pdf_path}")
        print(f"📊 Pages: {len(doc)}")
        
        # Extract text as markdown
        markdown_content = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extract text as markdown (this preserves structure)
            page_md = page.get_text("markdown")
            
            # Add page header for context
            markdown_content += f"\n\n## Page {page_num + 1}\n\n"
            markdown_content += page_md
            
            print(f"   ✅ Page {page_num + 1}: {len(page_md)} chars extracted")
        
        # Save markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        doc.close()
        
        print(f"✅ Markdown saved to: {output_path}")
        print(f"📊 Total content: {len(markdown_content):,} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analyze_markdown_structure(md_path: str):
    """Analyze the markdown structure to see what headers we have."""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all headers
    import re
    
    headers = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        # Look for markdown headers
        if line.startswith('#'):
            # Count header level
            level = 0
            for char in line:
                if char == '#':
                    level += 1
                else:
                    break
            
            title = line[level:].strip()
            
            headers.append({
                'line': line_num,
                'level': level,
                'title': title,
                'raw': line
            })
    
    print(f"\n📋 Markdown Structure Analysis:")
    print(f"   📊 Total headers: {len(headers)}")
    
    # Group by level
    level_counts = {}
    for header in headers:
        level = header['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level, count in sorted(level_counts.items()):
        print(f"   H{level}: {count} headers")
    
    # Show first 20 headers
    print(f"\n🔍 First 20 Headers:")
    for i, header in enumerate(headers[:20]):
        print(f"   {i+1:2d}. H{header['level']} - {header['title'][:60]}")
    
    return headers

if __name__ == "__main__":
    # Target PDF
    pdf_path = "./uploads/c132579d-416d-4178-bdca-c94b97bb076e/8726afa4-554d-42b9-b257-3d06e663b941_car24_chpt1_0.pdf"
    md_path = "car24_chpt1_0.md"
    
    print("🔄 PDF to Markdown Conversion using PyMuPDF")
    print("=" * 60)
    
    # Extract PDF as markdown
    if extract_pdf_as_markdown(pdf_path, md_path):
        # Analyze structure
        analyze_markdown_structure(md_path)
    else:
        print("❌ Failed to extract PDF")