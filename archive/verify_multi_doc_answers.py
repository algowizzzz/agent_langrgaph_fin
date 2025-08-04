#!/usr/bin/env python3
"""
Verify AI's multi-document answers by extracting and analyzing PDF content
"""

import fitz  # PyMuPDF
import re
from pathlib import Path

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            all_text += f"\n\n=== PAGE {page_num + 1} ===\n\n"
            all_text += page_text
        
        doc.close()
        print(f"✅ Extracted {len(all_text):,} characters from {pdf_path}")
        return all_text
        
    except Exception as e:
        print(f"❌ Error extracting {pdf_path}: {e}")
        return ""

def count_word_occurrences(text: str, word: str) -> int:
    """Count case-insensitive word occurrences."""
    # Use word boundaries to match whole words only
    pattern = r'\b' + re.escape(word) + r'\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return len(matches)

def find_cet_definition(text: str) -> str:
    """Find CET ratio definition in text."""
    # Look for CET1 or CET definitions
    patterns = [
        r'(.*CET1?.*[Cc]ommon [Ee]quity [Tt]ier.*)',
        r'(.*[Cc]ommon [Ee]quity [Tt]ier.*CET1?.*)',
        r'(CET1?.*stands for.*)',
        r'(CET1?.*means.*)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            return matches[0]
    
    return "Definition not found"

def analyze_chapter_content(text: str, chapter_name: str) -> dict:
    """Analyze chapter content and extract key information."""
    
    # Count pages
    page_count = len(re.findall(r'=== PAGE \d+ ===', text))
    
    # Look for key regulatory terms
    key_terms = {
        'capital': count_word_occurrences(text, 'capital'),
        'risk': count_word_occurrences(text, 'risk'),
        'CET1': count_word_occurrences(text, 'CET1'),
        'CCP': count_word_occurrences(text, 'CCP'),
        'counterparty': count_word_occurrences(text, 'counterparty'),
        'settlement': count_word_occurrences(text, 'settlement')
    }
    
    # Extract chapter title/subject
    title_match = re.search(r'(Chapter \d+.*)', text, re.IGNORECASE)
    chapter_title = title_match.group(1) if title_match else "Title not found"
    
    return {
        'chapter_name': chapter_name,
        'page_count': page_count,
        'character_count': len(text),
        'word_count': len(text.split()),
        'chapter_title': chapter_title,
        'key_terms': key_terms
    }

def main():
    """Main analysis function."""
    
    print("🔍 VERIFYING AI'S MULTI-DOCUMENT ANSWERS")
    print("="*50)
    
    # Extract text from both PDFs
    chap1_text = extract_pdf_text("car24_chpt1_0.pdf")
    chap7_text = extract_pdf_text("car24_chpt7.pdf")
    
    if not chap1_text or not chap7_text:
        print("❌ Failed to extract text from one or both PDFs")
        return
    
    # Analyze each chapter
    chap1_analysis = analyze_chapter_content(chap1_text, "Chapter 1")
    chap7_analysis = analyze_chapter_content(chap7_text, "Chapter 7")
    
    print("\n📊 CHAPTER ANALYSIS:")
    print(f"Chapter 1: {chap1_analysis['page_count']} pages, {chap1_analysis['word_count']:,} words")
    print(f"Chapter 7: {chap7_analysis['page_count']} pages, {chap7_analysis['word_count']:,} words")
    
    # QUESTION 1: Count "risk" mentions across both documents
    risk_chap1 = chap1_analysis['key_terms']['risk']
    risk_chap7 = chap7_analysis['key_terms']['risk']
    total_risk = risk_chap1 + risk_chap7
    
    print(f"\n📝 QUESTION 1 VERIFICATION: 'How many times is risk mentioned?'")
    print(f"AI Answer: 99 times")
    print(f"Actual Count:")
    print(f"  Chapter 1: {risk_chap1} mentions")
    print(f"  Chapter 7: {risk_chap7} mentions")
    print(f"  TOTAL: {total_risk} mentions")
    print(f"✅ ACCURACY: {'CORRECT' if total_risk == 99 else 'INCORRECT'} (diff: {abs(total_risk - 99)})")
    
    # QUESTION 2: CET ratio definition
    cet_definition = find_cet_definition(chap1_text + chap7_text)
    
    print(f"\n📝 QUESTION 2 VERIFICATION: 'What does CET ratio stand for?'")
    print(f"AI Answer: Common Equity Tier 1 ratio")
    print(f"Found in text: {cet_definition[:200]}...")
    
    contains_common_equity = 'common equity tier' in cet_definition.lower()
    print(f"✅ ACCURACY: {'CORRECT' if contains_common_equity else 'INCORRECT'}")
    
    # QUESTION 4: Document summary analysis
    print(f"\n📝 QUESTION 4 VERIFICATION: 'Summarize for business grad'")
    print(f"AI Summary: Settlement & Counterparty Risk Management Framework")
    
    # Check if Chapter 7 is actually about settlement and counterparty risk
    chap7_title = chap7_analysis['chapter_title']
    settlement_mentions = chap7_analysis['key_terms']['settlement']
    counterparty_mentions = chap7_analysis['key_terms']['counterparty']
    
    print(f"Chapter 7 Title: {chap7_title}")
    print(f"Settlement mentions: {settlement_mentions}")
    print(f"Counterparty mentions: {counterparty_mentions}")
    
    title_match = ('settlement' in chap7_title.lower() or 'counterparty' in chap7_title.lower())
    content_match = (settlement_mentions > 5 and counterparty_mentions > 5)
    
    print(f"✅ TITLE ACCURACY: {'CORRECT' if title_match else 'INCORRECT'}")
    print(f"✅ CONTENT FOCUS: {'CORRECT' if content_match else 'INCORRECT'}")
    
    # Save extracted text for manual review
    with open("extracted_chap1.txt", "w", encoding="utf-8") as f:
        f.write(chap1_text)
    
    with open("extracted_chap7.txt", "w", encoding="utf-8") as f:
        f.write(chap7_text)
    
    print(f"\n💾 Full text saved to: extracted_chap1.txt and extracted_chap7.txt")
    
    # Final assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"Question 1 (Risk count): {'✅ ACCURATE' if total_risk == 99 else '❌ INACCURATE'}")
    print(f"Question 2 (CET definition): {'✅ ACCURATE' if contains_common_equity else '❌ INACCURATE'}")
    print(f"Question 4 (Summary focus): {'✅ ACCURATE' if title_match and content_match else '❌ PARTIALLY ACCURATE'}")

if __name__ == "__main__":
    main()