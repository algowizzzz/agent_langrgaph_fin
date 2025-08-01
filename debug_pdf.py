#!/usr/bin/env python3
"""
Debug PDF extraction with PyMuPDF
"""

import fitz  # PyMuPDF
import sys
import traceback
from pathlib import Path

def debug_pdf_extraction(pdf_path: str):
    """Debug PDF extraction step by step."""
    
    try:
        print(f"🔍 Step 1: Checking file exists...")
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return False
        print(f"✅ File exists: {Path(pdf_path).stat().st_size} bytes")
        
        print(f"🔍 Step 2: Opening PDF...")
        doc = fitz.open(pdf_path)
        print(f"✅ PDF opened successfully")
        print(f"   📊 Pages: {len(doc)}")
        print(f"   📋 Metadata: {doc.metadata}")
        
        print(f"🔍 Step 3: Testing page access...")
        if len(doc) > 0:
            page = doc.load_page(0)
            print(f"✅ First page loaded")
            print(f"   📏 Page size: {page.rect}")
            
            print(f"🔍 Step 4: Testing text extraction methods...")
            
            # Try simple text extraction first
            simple_text = page.get_text()
            print(f"✅ Simple text: {len(simple_text)} chars")
            
            # Try markdown extraction
            try:
                md_text = page.get_text("markdown")
                print(f"✅ Markdown text: {len(md_text)} chars")
                
                # Show first 500 chars
                print(f"\n📝 First 500 chars of markdown:")
                print(repr(md_text[:500]))
                
            except Exception as e:
                print(f"❌ Markdown extraction failed: {e}")
                
        doc.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return False

def simple_text_extraction(pdf_path: str, output_path: str):
    """Simple text extraction without markdown formatting."""
    
    try:
        doc = fitz.open(pdf_path)
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            all_text += f"\n\n=== PAGE {page_num + 1} ===\n\n"
            all_text += page_text
            
            print(f"   Page {page_num + 1}: {len(page_text)} chars")
        
        # Save text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(all_text)
        
        doc.close()
        
        print(f"✅ Text saved to: {output_path}")
        print(f"📊 Total: {len(all_text):,} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    pdf_path = "./uploads/c132579d-416d-4178-bdca-c94b97bb076e/8726afa4-554d-42b9-b257-3d06e663b941_car24_chpt1_0.pdf"
    
    print("🔧 PDF Extraction Debug")
    print("=" * 50)
    
    if debug_pdf_extraction(pdf_path):
        print(f"\n🔄 Attempting simple text extraction...")
        simple_text_extraction(pdf_path, "car24_chpt1_0_simple.txt")