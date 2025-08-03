#!/usr/bin/env python3
"""
Quick extraction of Chapter 7 text using production_chunker logic
"""

import fitz  # PyMuPDF

def extract_chap7_text():
    """Extract text from car24_chpt7.pdf"""
    
    try:
        doc = fitz.open("car24_chpt7.pdf")
        
        all_text = ""
        page_count = len(doc)
        
        print(f"📄 Chapter 7: {page_count} pages")
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            all_text += f"\n\n=== PAGE {page_num + 1} ===\n\n"
            all_text += page_text
        
        doc.close()
        
        # Save to file
        with open("car24_chpt7_extracted.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        
        # Quick analysis
        risk_count = all_text.lower().count("risk")
        ccp_count = all_text.lower().count("ccp")
        settlement_count = all_text.lower().count("settlement")
        counterparty_count = all_text.lower().count("counterparty")
        
        print(f"✅ Chapter 7 extracted: {len(all_text):,} characters")
        print(f"📊 Risk mentions: {risk_count}")
        print(f"📊 CCP mentions: {ccp_count}")
        print(f"📊 Settlement mentions: {settlement_count}")
        print(f"📊 Counterparty mentions: {counterparty_count}")
        
        return all_text, risk_count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return "", 0

if __name__ == "__main__":
    extract_chap7_text()