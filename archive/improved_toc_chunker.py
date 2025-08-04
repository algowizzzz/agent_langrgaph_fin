#!/usr/bin/env python3
"""
Improved TOC-Based Chunker
Uses manual TOC mapping + enhanced pattern detection for proper hierarchical chunking.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

sys.path.append('.')
from tools.document_tools import document_chunk_store

class ImprovedTOCChunker:
    """Enhanced chunker based on actual Table of Contents structure."""
    
    def __init__(self):
        # Manual TOC mapping based on the provided Table of Contents image
        self.toc_structure = [
            {"section": "1.1", "title": "Scope of Application", "page": 4},
            {"section": "1.2", "title": "Regulatory Capital", "page": 4},
            {"section": "1.3", "title": "Total Risk weighted Assets", "page": 5},
            {"section": "1.3.1", "title": "Credit Risk", "page": 5},
            {"section": "1.3.2", "title": "Market Risk", "page": 7},
            {"section": "1.3.3", "title": "Operational Risk", "page": 7},
            {"section": "1.4", "title": "Approval to use Internal Model Based Approaches", "page": 8},
            {"section": "1.4.1", "title": "Approval to use the IRB Approaches to Credit Risk", "page": 8},
            {"section": "1.5", "title": "Capital Floor–Internal Model Based Approaches", "page": 9},
            {"section": "1.5.1", "title": "The Capital Floor", "page": 9},
            {"section": "1.5.2", "title": "Adjusted Capital Requirement", "page": 11},
            {"section": "1.6", "title": "Calculation of OSFI Minimum Capital Requirements", "page": 11},
            {"section": "1.6.1", "title": "Risk-Based Capital Ratios for D-SIBs and Category I and II SMSBs", "page": 11},
            {"section": "1.6.2", "title": "Simplified Risk-Based Capital Ratio for Category III SMSBs", "page": 12},
            {"section": "1.7", "title": "Mandated Capital Buffers", "page": 12},
            {"section": "1.7.1", "title": "Capital Conservation Buffer", "page": 13},
            {"section": "1.7.2", "title": "Countercyclical Buffer", "page": 15},
            {"section": "1.8", "title": "Domestic Systemically Important Bank (D-SIB) Surcharge", "page": 18},
            {"section": "1.9", "title": "Domestic Stability Buffer", "page": 19},
            {"section": "1.10", "title": "Capital Targets", "page": 20},
            {"section": "Annex 1", "title": "Domestic Systemic Importance and Capital Targets", "page": 22},
            {"section": "Annex 2", "title": "Supervisory Target Capital Requirements", "page": 26}
        ]
        
        # Enhanced patterns for detecting sections in various formats
        self.section_patterns = [
            r'^(\d+\.\d+\.\d+\.\d+)\.?\s*(.+)$',  # 1.1.1.1 pattern
            r'^(\d+\.\d+\.\d+)\.?\s*(.+)$',       # 1.1.1 pattern  
            r'^(\d+\.\d+)\.?\s*(.+)$',            # 1.1 pattern
            r'^(\d+)\.?\s*(.+)$',                 # 1. pattern
            r'^(Annex\s+\d+)\.?\s*(.+)$',         # Annex 1 pattern
        ]
    
    def extract_improved_toc_structure(self, doc_name: str) -> Dict:
        """Extract sections using improved pattern matching + TOC mapping."""
        
        if doc_name not in document_chunk_store:
            return {"error": f"Document {doc_name} not found"}
            
        chunks = document_chunk_store[doc_name]
        
        # Reconstruct full document text
        full_text = ""
        for chunk in chunks:
            full_text += chunk.get('page_content', '') + "\n"
        
        print(f"🔍 Analyzing document with improved TOC detection: {doc_name}")
        print(f"📊 Total document length: {len(full_text)} characters")
        print(f"📋 Expected TOC sections: {len(self.toc_structure)}")
        
        # Find content boundaries using multiple strategies
        sections = self._find_sections_multi_strategy(full_text)
        
        return {
            "document": doc_name,
            "total_chars": len(full_text),
            "expected_toc": self.toc_structure,
            "detected_sections": sections,
            "structure_analysis": self._analyze_improved_structure(sections)
        }
    
    def _find_sections_multi_strategy(self, full_text: str) -> List[Dict]:
        """Use multiple strategies to find section boundaries."""
        
        lines = full_text.split('\n')
        
        # Strategy 1: Look for exact TOC patterns in text
        toc_matches = self._find_toc_exact_matches(lines)
        
        # Strategy 2: Look for section content by keywords
        keyword_matches = self._find_by_section_keywords(lines)
        
        # Strategy 3: Look for page boundaries + content analysis
        page_content_matches = self._find_by_page_content_analysis(lines)
        
        # Combine and deduplicate strategies
        all_matches = []
        
        # Start with TOC exact matches (highest confidence)
        for match in toc_matches:
            all_matches.append({
                **match,
                'detection_method': 'toc_exact',
                'confidence': 'high'
            })
        
        # Add keyword matches for missing sections
        detected_sections = {m['section_number'] for m in all_matches}
        for match in keyword_matches:
            if match['section_number'] not in detected_sections:
                all_matches.append({
                    **match,
                    'detection_method': 'keyword',
                    'confidence': 'medium'
                })
                detected_sections.add(match['section_number'])
        
        # Add page content matches for remaining
        for match in page_content_matches:
            if match['section_number'] not in detected_sections:
                all_matches.append({
                    **match,
                    'detection_method': 'page_analysis',
                    'confidence': 'low'
                })
        
        return sorted(all_matches, key=lambda x: self._get_section_sort_key(x['section_number']))
    
    def _find_toc_exact_matches(self, lines: List[str]) -> List[Dict]:
        """Look for exact section number patterns in text."""
        
        matches = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            for pattern in self.section_patterns:
                match = re.match(pattern, line)
                if match:
                    section_number = match.group(1)
                    title = match.group(2).strip()
                    
                    # Check if this matches our expected TOC
                    toc_entry = self._find_toc_entry(section_number)
                    if toc_entry:
                        # Extract content for this section
                        content = self._extract_section_content(lines, line_num, section_number)
                        
                        matches.append({
                            'section_number': section_number,
                            'title': title,
                            'expected_title': toc_entry['title'],
                            'start_line': line_num,
                            'content': content,
                            'word_count': len(content.split()),
                            'toc_page': toc_entry['page'],
                            'hierarchy': self._parse_section_hierarchy(section_number)
                        })
        
        return matches
    
    def _find_by_section_keywords(self, lines: List[str]) -> List[Dict]:
        """Find sections by searching for title keywords."""
        
        matches = []
        
        for toc_entry in self.toc_structure:
            section_number = toc_entry['section']
            expected_title = toc_entry['title']
            
            # Create keyword search patterns
            title_keywords = self._extract_keywords(expected_title)
            
            # Search for lines containing these keywords
            best_match = None
            best_score = 0
            
            for line_num, line in enumerate(lines):
                line = line.strip().lower()
                score = 0
                
                for keyword in title_keywords:
                    if keyword.lower() in line:
                        score += 1
                
                # Also check for section number patterns
                if section_number.replace('.', '\\.') in line or section_number.replace('.', ' ') in line:
                    score += 2
                
                if score > best_score and score >= 2:  # Minimum threshold
                    best_score = score
                    best_match = line_num
            
            if best_match is not None:
                content = self._extract_section_content(lines, best_match, section_number)
                
                matches.append({
                    'section_number': section_number,
                    'title': expected_title,
                    'expected_title': expected_title,
                    'start_line': best_match,
                    'content': content,
                    'word_count': len(content.split()),
                    'toc_page': toc_entry['page'],
                    'hierarchy': self._parse_section_hierarchy(section_number),
                    'keyword_score': best_score
                })
        
        return matches
    
    def _find_by_page_content_analysis(self, lines: List[str]) -> List[Dict]:
        """Analyze content by page boundaries and infer sections."""
        
        matches = []
        
        # Find page boundaries
        page_boundaries = []
        for line_num, line in enumerate(lines):
            if re.match(r'^##\s*Page\s+\d+', line.strip()):
                page_match = re.match(r'^##\s*Page\s+(\d+)', line.strip())
                if page_match:
                    page_boundaries.append({
                        'line_num': line_num,
                        'page_num': int(page_match.group(1))
                    })
        
        # Map TOC entries to page ranges
        for toc_entry in self.toc_structure:
            section_number = toc_entry['section']
            expected_page = toc_entry['page']
            
            # Find closest page boundary
            closest_page = None
            for boundary in page_boundaries:
                if boundary['page_num'] >= expected_page:
                    closest_page = boundary
                    break
            
            if closest_page:
                # Extract content from this page area
                start_line = closest_page['line_num']
                end_line = start_line + 100  # Look ahead reasonable amount
                
                content_lines = lines[start_line:min(end_line, len(lines))]
                content = '\n'.join(content_lines)
                
                matches.append({
                    'section_number': section_number,
                    'title': toc_entry['title'],
                    'expected_title': toc_entry['title'],
                    'start_line': start_line,
                    'content': content,
                    'word_count': len(content.split()),
                    'toc_page': toc_entry['page'],
                    'hierarchy': self._parse_section_hierarchy(section_number),
                    'estimated_from_page': expected_page
                })
        
        return matches
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from section titles."""
        
        # Remove common words and extract key terms
        stop_words = {'the', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'a', 'an'}
        words = re.findall(r'\b\w+\b', title.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        return keywords[:3]  # Top 3 keywords
    
    def _find_toc_entry(self, section_number: str) -> Optional[Dict]:
        """Find TOC entry by section number."""
        
        for entry in self.toc_structure:
            if entry['section'] == section_number:
                return entry
        return None
    
    def _extract_section_content(self, lines: List[str], start_line: int, section_number: str) -> str:
        """Extract content for a section until the next section or end."""
        
        content_lines = []
        
        # Look ahead to find the end of this section
        for i in range(start_line, min(start_line + 200, len(lines))):
            line = lines[i].strip()
            
            # Stop if we hit another section
            if i > start_line:
                for pattern in self.section_patterns:
                    if re.match(pattern, line):
                        # Check if this is a different section
                        match = re.match(pattern, line)
                        if match and match.group(1) != section_number:
                            return '\n'.join(content_lines)
            
            content_lines.append(lines[i])
        
        return '\n'.join(content_lines)
    
    def _parse_section_hierarchy(self, section_number: str) -> Dict:
        """Parse section number into hierarchy."""
        
        if section_number.startswith('Annex'):
            return {
                'section': section_number,
                'subsection': None,
                'sub_subsection': None,
                'level': 1
            }
        
        parts = section_number.split('.')
        hierarchy = {
            'section': None,
            'subsection': None,
            'sub_subsection': None,
            'sub_sub_subsection': None,
            'level': len(parts)
        }
        
        if len(parts) >= 1:
            hierarchy['section'] = parts[0]
        if len(parts) >= 2:
            hierarchy['subsection'] = f"{parts[0]}.{parts[1]}"
        if len(parts) >= 3:
            hierarchy['sub_subsection'] = f"{parts[0]}.{parts[1]}.{parts[2]}"
        if len(parts) >= 4:
            hierarchy['sub_sub_subsection'] = section_number
        
        return hierarchy
    
    def _get_section_sort_key(self, section_number: str) -> tuple:
        """Create sort key for section numbers."""
        
        if section_number.startswith('Annex'):
            # Annexes come last
            annex_num = re.findall(r'\d+', section_number)
            return (999, int(annex_num[0]) if annex_num else 0)
        
        # Regular numbered sections
        parts = section_number.split('.')
        # Pad with zeros to ensure proper sorting
        padded_parts = []
        for part in parts:
            try:
                padded_parts.append(int(part))
            except ValueError:
                padded_parts.append(0)
        
        # Ensure we have at least 4 levels for consistent sorting
        while len(padded_parts) < 4:
            padded_parts.append(0)
        
        return tuple(padded_parts)
    
    def _analyze_improved_structure(self, sections: List[Dict]) -> Dict:
        """Analyze the improved structure results."""
        
        analysis = {
            'total_detected': len(sections),
            'expected_total': len(self.toc_structure),
            'detection_methods': defaultdict(int),
            'confidence_levels': defaultdict(int),
            'coverage_analysis': {},
            'word_count_stats': {}
        }
        
        # Count detection methods and confidence
        for section in sections:
            method = section.get('detection_method', 'unknown')
            confidence = section.get('confidence', 'unknown')
            analysis['detection_methods'][method] += 1
            analysis['confidence_levels'][confidence] += 1
        
        # Coverage analysis
        detected_sections = {s['section_number'] for s in sections}
        expected_sections = {e['section'] for e in self.toc_structure}
        
        analysis['coverage_analysis'] = {
            'detected': list(detected_sections),
            'expected': list(expected_sections),
            'missing': list(expected_sections - detected_sections),
            'extra': list(detected_sections - expected_sections),
            'coverage_percent': len(detected_sections & expected_sections) / len(expected_sections) * 100
        }
        
        # Word count statistics
        word_counts = [s['word_count'] for s in sections if s['word_count'] > 0]
        if word_counts:
            analysis['word_count_stats'] = {
                'total_words': sum(word_counts),
                'avg_words': sum(word_counts) / len(word_counts),
                'min_words': min(word_counts),
                'max_words': max(word_counts),
                'sections_with_content': len(word_counts)
            }
        
        return analysis
    
    def create_improved_toc_chunks(self, doc_name: str, strategy: str = "high_confidence") -> Dict:
        """Create chunks using improved TOC detection."""
        
        structure = self.extract_improved_toc_structure(doc_name)
        if "error" in structure:
            return structure
        
        sections = structure["detected_sections"]
        
        # Filter sections based on strategy
        if strategy == "high_confidence":
            filtered_sections = [s for s in sections if s.get('confidence') == 'high']
        elif strategy == "medium_plus":
            filtered_sections = [s for s in sections if s.get('confidence') in ['high', 'medium']]
        else:  # all
            filtered_sections = sections
        
        # If we don't have enough high-confidence sections, fall back
        if len(filtered_sections) < 5:
            filtered_sections = sections
        
        chunks = []
        
        for i, section in enumerate(filtered_sections):
            chunk = {
                'chunk_index': i,
                'section_number': section['section_number'],
                'title': section['title'],
                'expected_title': section.get('expected_title', section['title']),
                'content': section['content'],
                'word_count': section['word_count'],
                'hierarchy': section['hierarchy'],
                'toc_page': section.get('toc_page'),
                'detection_method': section.get('detection_method'),
                'confidence': section.get('confidence'),
                'metadata': {
                    'source': doc_name,
                    'file_type': 'PDF',
                    'chunk_type': 'improved_toc',
                    'section_hierarchy': section['hierarchy'],
                    'detection_confidence': section.get('confidence'),
                    'expected_page': section.get('toc_page')
                }
            }
            
            chunks.append(chunk)
        
        return {
            'document': doc_name,
            'chunking_strategy': f'improved_toc_{strategy}',
            'total_chunks': len(chunks),
            'chunks': chunks,
            'index': self._create_improved_index(chunks),
            'detection_analysis': structure
        }
    
    def _create_improved_index(self, chunks: List[Dict]) -> Dict:
        """Create improved searchable index."""
        
        index = {
            'by_section_number': {},
            'by_hierarchy_level': defaultdict(list),
            'by_title_keywords': defaultdict(list),
            'by_page': defaultdict(list),
            'chunk_summary': [],
            'section_map': {}
        }
        
        for chunk in chunks:
            chunk_id = chunk['chunk_index']
            section_number = chunk['section_number']
            hierarchy = chunk['hierarchy']
            
            # Section number index
            index['by_section_number'][section_number] = chunk_id
            
            # Hierarchy level index
            level = hierarchy.get('level', 1)
            index['by_hierarchy_level'][f'level_{level}'].append(chunk_id)
            
            # Title keyword index
            title_words = chunk['title'].lower().split()
            for word in title_words:
                if len(word) > 3:
                    index['by_title_keywords'][word].append(chunk_id)
            
            # Page index
            if chunk.get('toc_page'):
                index['by_page'][chunk['toc_page']].append(chunk_id)
            
            # Summary
            index['chunk_summary'].append({
                'chunk_id': chunk_id,
                'section_number': section_number,
                'title': chunk['title'],
                'word_count': chunk['word_count'],
                'page': chunk.get('toc_page'),
                'confidence': chunk.get('confidence')
            })
            
            # Section mapping
            index['section_map'][section_number] = {
                'chunk_id': chunk_id,
                'title': chunk['title'],
                'hierarchy_path': self._build_hierarchy_path(hierarchy)
            }
        
        return index
    
    def _build_hierarchy_path(self, hierarchy: Dict) -> str:
        """Build readable hierarchy path."""
        
        parts = []
        if hierarchy.get('section'):
            parts.append(hierarchy['section'])
        if hierarchy.get('subsection'):
            parts.append(hierarchy['subsection'])
        if hierarchy.get('sub_subsection'):
            parts.append(hierarchy['sub_subsection'])
        
        return ' > '.join(parts) if parts else 'Root'

def main():
    """Run improved TOC-based chunking analysis."""
    
    chunker = ImprovedTOCChunker()
    
    # Target document
    doc_name = "8726afa4-554d-42b9-b257-3d06e663b941_car24_chpt1_0.pdf"
    
    print("🔍 STEP 1: Improved TOC Structure Detection")
    print("=" * 60)
    
    structure = chunker.extract_improved_toc_structure(doc_name)
    
    if "error" in structure:
        print(f"❌ {structure['error']}")
        return
    
    analysis = structure['structure_analysis']
    
    print(f"📊 Detection Results:")
    print(f"   📄 Document: {structure['document']}")
    print(f"   📏 Total chars: {structure['total_chars']:,}")
    print(f"   🎯 Expected sections: {analysis['expected_total']}")
    print(f"   ✅ Detected sections: {analysis['total_detected']}")
    print(f"   📈 Coverage: {analysis['coverage_analysis']['coverage_percent']:.1f}%")
    
    # Detection method breakdown
    print(f"\n📋 Detection Methods:")
    for method, count in analysis['detection_methods'].items():
        print(f"   {method}: {count} sections")
    
    # Show detected sections
    print(f"\n🔍 Detected Sections (first 10):")
    for i, section in enumerate(structure['detected_sections'][:10]):
        confidence = section.get('confidence', 'unknown')
        method = section.get('detection_method', 'unknown')
        print(f"   {section['section_number']}: {section['title'][:50]}... ({confidence}, {method})")
    
    # Missing sections
    missing = analysis['coverage_analysis']['missing']
    if missing:
        print(f"\n❌ Missing Sections: {missing}")
    
    print(f"\n🔍 STEP 2: Creating Improved TOC Chunks")
    print("=" * 60)
    
    # Create chunks with high confidence strategy
    chunks_result = chunker.create_improved_toc_chunks(doc_name, "medium_plus")
    
    print(f"✅ Improved TOC Chunking Complete:")
    print(f"   📦 Total chunks: {chunks_result['total_chunks']}")
    print(f"   📊 Strategy: {chunks_result['chunking_strategy']}")
    
    # Save results
    with open("chunks_2025-01-31/improved_toc_analysis.json", "w") as f:
        json.dump(structure, f, indent=2)
    
    with open("chunks_2025-01-31/improved_toc_chunks.json", "w") as f:
        json.dump(chunks_result, f, indent=2)
    
    with open("chunks_2025-01-31/improved_toc_index.json", "w") as f:
        json.dump(chunks_result['index'], f, indent=2)
    
    # Create summary
    summary = []
    summary.append("# Improved Table of Contents-Based Chunks\n")
    summary.append(f"**Document**: {doc_name}\n")
    summary.append(f"**Strategy**: {chunks_result['chunking_strategy']}\n")
    summary.append(f"**Total Chunks**: {chunks_result['total_chunks']}\n")
    summary.append(f"**Coverage**: {analysis['coverage_analysis']['coverage_percent']:.1f}%\n\n")
    
    summary.append("## Chunk Overview\n")
    for chunk in chunks_result['chunks']:
        hierarchy_path = chunker._build_hierarchy_path(chunk['hierarchy'])
        confidence = chunk.get('confidence', 'unknown')
        
        summary.append(f"**{chunk['section_number']}**: {chunk['title']}\n")
        summary.append(f"- Hierarchy: {hierarchy_path}\n")
        summary.append(f"- Words: {chunk['word_count']}\n")
        summary.append(f"- Page: {chunk.get('toc_page', 'Unknown')}\n")
        summary.append(f"- Confidence: {confidence}\n")
        summary.append(f"- Preview: {chunk['content'][:200]}...\n\n")
    
    with open("chunks_2025-01-31/improved_toc_summary.md", "w") as f:
        f.write(''.join(summary))
    
    print(f"\n📁 Improved TOC Files Created:")
    print(f"   📋 improved_toc_analysis.json - Detection analysis")
    print(f"   📦 improved_toc_chunks.json - TOC-based chunks")
    print(f"   🗂️ improved_toc_index.json - Enhanced search index")
    print(f"   📖 improved_toc_summary.md - Human-readable summary")

if __name__ == "__main__":
    main()