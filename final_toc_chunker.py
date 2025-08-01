#!/usr/bin/env python3
"""
Final TOC-Based Chunker
Clean, deduplicated chunks based on Table of Contents structure.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

sys.path.append('.')
from tools.document_tools import document_chunk_store

class FinalTOCChunker:
    """Final refined chunker for clean TOC-based sections."""
    
    def __init__(self):
        # Manual TOC mapping from the provided image
        self.toc_structure = [
            {"section": "1.1", "title": "Scope of Application", "page": 4, "level": 2},
            {"section": "1.2", "title": "Regulatory Capital", "page": 4, "level": 2},
            {"section": "1.3", "title": "Total Risk weighted Assets", "page": 5, "level": 2},
            {"section": "1.3.1", "title": "Credit Risk", "page": 5, "level": 3},
            {"section": "1.3.2", "title": "Market Risk", "page": 7, "level": 3},
            {"section": "1.3.3", "title": "Operational Risk", "page": 7, "level": 3},
            {"section": "1.4", "title": "Approval to use Internal Model Based Approaches", "page": 8, "level": 2},
            {"section": "1.4.1", "title": "Approval to use the IRB Approaches to Credit Risk", "page": 8, "level": 3},
            {"section": "1.5", "title": "Capital Floor–Internal Model Based Approaches", "page": 9, "level": 2},
            {"section": "1.5.1", "title": "The Capital Floor", "page": 9, "level": 3},
            {"section": "1.5.2", "title": "Adjusted Capital Requirement", "page": 11, "level": 3},
            {"section": "1.6", "title": "Calculation of OSFI Minimum Capital Requirements", "page": 11, "level": 2},
            {"section": "1.6.1", "title": "Risk-Based Capital Ratios for D-SIBs and Category I and II SMSBs", "page": 11, "level": 3},
            {"section": "1.6.2", "title": "Simplified Risk-Based Capital Ratio for Category III SMSBs", "page": 12, "level": 3},
            {"section": "1.7", "title": "Mandated Capital Buffers", "page": 12, "level": 2},
            {"section": "1.7.1", "title": "Capital Conservation Buffer", "page": 13, "level": 3},
            {"section": "1.7.2", "title": "Countercyclical Buffer", "page": 15, "level": 3},
            {"section": "1.8", "title": "Domestic Systemically Important Bank (D-SIB) Surcharge", "page": 18, "level": 2},
            {"section": "1.9", "title": "Domestic Stability Buffer", "page": 19, "level": 2},
            {"section": "1.10", "title": "Capital Targets", "page": 20, "level": 2},
            {"section": "Annex 1", "title": "Domestic Systemic Importance and Capital Targets", "page": 22, "level": 1},
            {"section": "Annex 2", "title": "Supervisory Target Capital Requirements", "page": 26, "level": 1}
        ]
    
    def create_final_toc_chunks(self, doc_name: str) -> Dict:
        """Create final, clean TOC-based chunks."""
        
        if doc_name not in document_chunk_store:
            return {"error": f"Document {doc_name} not found"}
            
        chunks = document_chunk_store[doc_name]
        
        # Reconstruct full document text
        full_text = ""
        for chunk in chunks:
            full_text += chunk.get('page_content', '') + "\n"
        
        print(f"🔍 Creating final TOC-based chunks for: {doc_name}")
        print(f"📊 Document length: {len(full_text):,} characters")
        print(f"📋 Target sections: {len(self.toc_structure)}")
        
        # Extract sections using smart content mapping
        final_sections = self._extract_final_sections(full_text)
        
        # Create clean chunks
        chunks = []
        total_words = 0
        
        for i, section in enumerate(final_sections):
            chunk = {
                'chunk_index': i,
                'section_number': section['section_number'],
                'title': section['title'],
                'level': section['level'],
                'content': section['content'],
                'word_count': section['word_count'],
                'char_count': len(section['content']),
                'page': section['page'],
                'hierarchy': self._parse_hierarchy(section['section_number']),
                'metadata': {
                    'source': doc_name,
                    'file_type': 'PDF',
                    'chunk_type': 'final_toc',
                    'section_level': section['level'],
                    'expected_page': section['page'],
                    'section_hierarchy': self._parse_hierarchy(section['section_number'])
                }
            }
            
            chunks.append(chunk)
            total_words += section['word_count']
        
        return {
            'document': doc_name,
            'chunking_strategy': 'final_toc_based',
            'total_chunks': len(chunks),
            'total_words': total_words,
            'avg_words_per_chunk': total_words / len(chunks) if chunks else 0,
            'chunks': chunks,
            'index': self._create_final_index(chunks),
            'quality_metrics': self._calculate_quality_metrics(chunks)
        }
    
    def _extract_final_sections(self, full_text: str) -> List[Dict]:
        """Extract sections with smart content boundaries."""
        
        lines = full_text.split('\n')
        sections = []
        
        # Create ordered list by expected document flow
        ordered_toc = sorted(self.toc_structure, key=lambda x: (x['page'], self._get_section_sort_key(x['section'])))
        
        for i, toc_entry in enumerate(ordered_toc):
            section_number = toc_entry['section']
            expected_title = toc_entry['title']
            expected_page = toc_entry['page']
            level = toc_entry['level']
            
            print(f"   🔍 Extracting {section_number}: {expected_title}")
            
            # Find section content using multiple strategies
            content = self._find_section_content_smart(
                lines, 
                section_number, 
                expected_title, 
                expected_page,
                # Next section for boundary detection
                ordered_toc[i + 1] if i + 1 < len(ordered_toc) else None
            )
            
            word_count = len(content.split()) if content else 0
            
            if word_count > 0:  # Only include sections with content
                sections.append({
                    'section_number': section_number,
                    'title': expected_title,
                    'level': level,
                    'page': expected_page,
                    'content': content,
                    'word_count': word_count
                })
                print(f"      ✅ Found {word_count} words")
            else:
                print(f"      ❌ No content found")
        
        return sections
    
    def _find_section_content_smart(self, lines: List[str], section_number: str, 
                                  expected_title: str, expected_page: int,
                                  next_section: Optional[Dict] = None) -> str:
        """Smart content extraction using multiple clues."""
        
        # Strategy 1: Look for exact section number patterns
        exact_matches = self._find_exact_section_patterns(lines, section_number, expected_title)
        
        # Strategy 2: Find by page + title keywords
        page_matches = self._find_by_page_and_keywords(lines, expected_page, expected_title)
        
        # Strategy 3: Use content position estimation
        position_matches = self._find_by_position_estimation(lines, section_number, expected_page)
        
        # Choose best match
        best_content = ""
        max_words = 0
        
        for match in exact_matches + page_matches + position_matches:
            content = match.get('content', '')
            word_count = len(content.split())
            
            if word_count > max_words:
                max_words = word_count
                best_content = content
        
        # If still no good match, try broader search
        if max_words < 50:
            broad_content = self._find_by_broad_search(lines, expected_title, expected_page)
            if len(broad_content.split()) > max_words:
                best_content = broad_content
        
        # Clean up content
        return self._clean_section_content(best_content, section_number, next_section)
    
    def _find_exact_section_patterns(self, lines: List[str], section_number: str, expected_title: str) -> List[Dict]:
        """Find exact section number patterns."""
        
        matches = []
        
        # Patterns to look for
        patterns = [
            rf'^{re.escape(section_number)}\.?\s*{re.escape(expected_title)}',
            rf'^{re.escape(section_number)}\.?\s+(.{{0,100}})',  # Flexible title matching
            rf'^\s*{re.escape(section_number)}\s',  # Just section number
        ]
        
        for line_num, line in enumerate(lines):
            line_clean = line.strip()
            
            for pattern in patterns:
                if re.match(pattern, line_clean, re.IGNORECASE):
                    # Extract content from this point
                    content = self._extract_content_from_line(lines, line_num, section_number)
                    matches.append({
                        'type': 'exact_pattern',
                        'start_line': line_num,
                        'content': content,
                        'confidence': 'high'
                    })
                    break
        
        return matches
    
    def _find_by_page_and_keywords(self, lines: List[str], expected_page: int, expected_title: str) -> List[Dict]:
        """Find section by page boundary + title keywords."""
        
        matches = []
        
        # Find page boundaries
        page_boundaries = []
        for line_num, line in enumerate(lines):
            if re.match(r'^##\s*Page\s+\d+', line.strip()):
                page_match = re.match(r'^##\s*Page\s+(\d+)', line.strip())
                if page_match:
                    page_num = int(page_match.group(1))
                    page_boundaries.append((line_num, page_num))
        
        # Find closest page
        target_page_line = None
        for line_num, page_num in page_boundaries:
            if page_num >= expected_page:
                target_page_line = line_num
                break
        
        if target_page_line is not None:
            # Search around this page for title keywords
            title_keywords = self._extract_title_keywords(expected_title)
            
            search_start = max(0, target_page_line - 10)
            search_end = min(len(lines), target_page_line + 200)
            
            best_match_line = None
            best_score = 0
            
            for line_num in range(search_start, search_end):
                line = lines[line_num].strip().lower()
                score = 0
                
                for keyword in title_keywords:
                    if keyword.lower() in line:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match_line = line_num
            
            if best_match_line is not None and best_score >= 2:
                content = self._extract_content_from_line(lines, best_match_line, "")
                matches.append({
                    'type': 'page_keyword',
                    'start_line': best_match_line,
                    'content': content,
                    'confidence': 'medium',
                    'keyword_score': best_score
                })
        
        return matches
    
    def _find_by_position_estimation(self, lines: List[str], section_number: str, expected_page: int) -> List[Dict]:
        """Estimate section position based on document flow."""
        
        matches = []
        
        # Simple estimation: find content around expected page
        page_boundaries = []
        for line_num, line in enumerate(lines):
            if re.match(r'^##\s*Page\s+\d+', line.strip()):
                page_match = re.match(r'^##\s*Page\s+(\d+)', line.strip())
                if page_match:
                    page_num = int(page_match.group(1))
                    page_boundaries.append((line_num, page_num))
        
        # Find page range for this section
        start_line = None
        end_line = None
        
        for i, (line_num, page_num) in enumerate(page_boundaries):
            if page_num >= expected_page:
                start_line = line_num
                # End at next page or document end
                if i + 1 < len(page_boundaries):
                    end_line = page_boundaries[i + 1][0]
                else:
                    end_line = len(lines)
                break
        
        if start_line is not None:
            content_lines = lines[start_line:end_line] if end_line else lines[start_line:]
            content = '\n'.join(content_lines)
            
            matches.append({
                'type': 'position_estimation',
                'start_line': start_line,
                'content': content,
                'confidence': 'low'
            })
        
        return matches
    
    def _find_by_broad_search(self, lines: List[str], expected_title: str, expected_page: int) -> str:
        """Broad search fallback."""
        
        title_keywords = self._extract_title_keywords(expected_title)
        
        # Search entire document for best keyword match
        best_content = ""
        best_score = 0
        
        for line_num, line in enumerate(lines):
            line_lower = line.strip().lower()
            score = sum(1 for keyword in title_keywords if keyword.lower() in line_lower)
            
            if score > best_score:
                best_score = score
                # Extract content from this area
                start_line = max(0, line_num - 5)
                end_line = min(len(lines), line_num + 100)
                content = '\n'.join(lines[start_line:end_line])
                best_content = content
        
        return best_content
    
    def _extract_content_from_line(self, lines: List[str], start_line: int, section_number: str) -> str:
        """Extract content from a starting line until next section."""
        
        content_lines = []
        
        # Look ahead to find natural ending
        for i in range(start_line, min(start_line + 300, len(lines))):
            line = lines[i].strip()
            
            # Stop at next major section
            if i > start_line + 10:  # Give some buffer
                # Check for section patterns that would indicate next section
                if re.match(r'^\d+\.\d+\.?\s', line) or re.match(r'^##\s*Page\s+\d+', line):
                    break
            
            content_lines.append(lines[i])
        
        return '\n'.join(content_lines)
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from titles."""
        
        stop_words = {'the', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'a', 'an', 'use', 'based'}
        words = re.findall(r'\b\w+\b', title.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        return keywords[:4]  # Top 4 keywords
    
    def _clean_section_content(self, content: str, section_number: str, next_section: Optional[Dict]) -> str:
        """Clean and truncate section content appropriately."""
        
        if not content:
            return ""
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at start
            if not cleaned_lines and not line:
                continue
            
            # Stop at obvious next section boundaries
            if next_section and line.startswith(next_section['section']):
                break
            
            cleaned_lines.append(line)
        
        # Limit content size (reasonable chunk size)
        content = '\n'.join(cleaned_lines)
        
        # Truncate if too long (keep first 2000 words)
        words = content.split()
        if len(words) > 2000:
            content = ' '.join(words[:2000]) + "\n\n[Content truncated for optimal chunk size]"
        
        return content
    
    def _parse_hierarchy(self, section_number: str) -> Dict:
        """Parse section hierarchy."""
        
        if section_number.startswith('Annex'):
            return {
                'section': section_number,
                'subsection': None,
                'sub_subsection': None,
                'level': 1
            }
        
        parts = section_number.split('.')
        return {
            'section': parts[0] if len(parts) >= 1 else None,
            'subsection': f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else None,
            'sub_subsection': f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else None,
            'level': len(parts)
        }
    
    def _get_section_sort_key(self, section_number: str) -> tuple:
        """Create sort key for proper section ordering."""
        
        if section_number.startswith('Annex'):
            annex_num = re.findall(r'\d+', section_number)
            return (999, int(annex_num[0]) if annex_num else 0, 0, 0)
        
        parts = section_number.split('.')
        padded = [int(p) for p in parts] + [0] * (4 - len(parts))
        return tuple(padded)
    
    def _create_final_index(self, chunks: List[Dict]) -> Dict:
        """Create final searchable index."""
        
        index = {
            'by_section': {},
            'by_level': defaultdict(list),
            'by_page': defaultdict(list),
            'by_keywords': defaultdict(list),
            'section_map': {},
            'chunk_summary': []
        }
        
        for chunk in chunks:
            chunk_id = chunk['chunk_index']
            section = chunk['section_number']
            level = chunk['level']
            page = chunk['page']
            title = chunk['title']
            
            # Direct section lookup
            index['by_section'][section] = chunk_id
            
            # Level grouping
            index['by_level'][f'level_{level}'].append(chunk_id)
            
            # Page grouping
            index['by_page'][page].append(chunk_id)
            
            # Title keywords
            keywords = self._extract_title_keywords(title)
            for keyword in keywords:
                index['by_keywords'][keyword].append(chunk_id)
            
            # Section mapping
            index['section_map'][section] = {
                'chunk_id': chunk_id,
                'title': title,
                'page': page,
                'word_count': chunk['word_count']
            }
            
            # Summary
            index['chunk_summary'].append({
                'chunk_id': chunk_id,
                'section': section,
                'title': title,
                'level': level,
                'page': page,
                'word_count': chunk['word_count'],
                'char_count': chunk['char_count']
            })
        
        return index
    
    def _calculate_quality_metrics(self, chunks: List[Dict]) -> Dict:
        """Calculate quality metrics for the chunking."""
        
        word_counts = [c['word_count'] for c in chunks]
        char_counts = [c['char_count'] for c in chunks]
        
        return {
            'total_sections': len(chunks),
            'total_words': sum(word_counts),
            'total_chars': sum(char_counts),
            'avg_words_per_section': sum(word_counts) / len(word_counts) if word_counts else 0,
            'min_words': min(word_counts) if word_counts else 0,
            'max_words': max(word_counts) if word_counts else 0,
            'word_distribution': {
                'small (0-100)': len([w for w in word_counts if w <= 100]),
                'medium (101-500)': len([w for w in word_counts if 101 <= w <= 500]),
                'large (501-1500)': len([w for w in word_counts if 501 <= w <= 1500]),
                'very_large (1500+)': len([w for w in word_counts if w > 1500])
            },
            'level_distribution': Counter([c['level'] for c in chunks]),
            'coverage_check': {
                'expected_sections': len(self.toc_structure),
                'actual_sections': len(chunks),
                'coverage_percent': len(chunks) / len(self.toc_structure) * 100
            }
        }

def main():
    """Create final TOC-based chunks."""
    
    chunker = FinalTOCChunker()
    
    # Target document
    doc_name = "8726afa4-554d-42b9-b257-3d06e663b941_car24_chpt1_0.pdf"
    
    print("🎯 FINAL TOC-BASED CHUNKING")
    print("=" * 60)
    
    result = chunker.create_final_toc_chunks(doc_name)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    metrics = result['quality_metrics']
    
    print(f"\n✅ Final Chunking Results:")
    print(f"   📦 Total chunks: {result['total_chunks']}")
    print(f"   📊 Total words: {result['total_words']:,}")
    print(f"   📈 Avg words/chunk: {result['avg_words_per_chunk']:.0f}")
    print(f"   🎯 Coverage: {metrics['coverage_check']['coverage_percent']:.1f}%")
    
    print(f"\n📊 Quality Metrics:")
    print(f"   📝 Word distribution:")
    for size, count in metrics['word_distribution'].items():
        print(f"      {size}: {count} sections")
    
    print(f"   📋 Level distribution:")
    for level, count in metrics['level_distribution'].items():
        print(f"      Level {level}: {count} sections")
    
    # Save final results
    with open("chunks_2025-01-31/final_toc_chunks.json", "w") as f:
        json.dump(result, f, indent=2)
    
    with open("chunks_2025-01-31/final_toc_index.json", "w") as f:
        json.dump(result['index'], f, indent=2)
    
    # Create final summary
    summary = []
    summary.append("# Final Table of Contents-Based Chunks\n")
    summary.append(f"**Document**: {result['document']}\n")
    summary.append(f"**Total Chunks**: {result['total_chunks']}\n")
    summary.append(f"**Total Words**: {result['total_words']:,}\n")
    summary.append(f"**Average Words/Chunk**: {result['avg_words_per_chunk']:.0f}\n")
    summary.append(f"**Coverage**: {metrics['coverage_check']['coverage_percent']:.1f}%\n\n")
    
    summary.append("## Section Overview\n")
    for chunk in result['chunks']:
        summary.append(f"**{chunk['section_number']}** - {chunk['title']}\n")
        summary.append(f"- Level: {chunk['level']} | Page: {chunk['page']} | Words: {chunk['word_count']:,}\n")
        summary.append(f"- Preview: {chunk['content'][:150]}...\n\n")
    
    with open("chunks_2025-01-31/final_toc_summary.md", "w") as f:
        f.write(''.join(summary))
    
    print(f"\n📁 Final Files Created:")
    print(f"   📦 final_toc_chunks.json - Clean TOC-based chunks")
    print(f"   🗂️ final_toc_index.json - Optimized search index")
    print(f"   📖 final_toc_summary.md - Executive summary")
    
    print(f"\n🎉 SUCCESS: Clean TOC-based chunking complete!")
    print(f"    Ready for integration with search tools!")

if __name__ == "__main__":
    main()