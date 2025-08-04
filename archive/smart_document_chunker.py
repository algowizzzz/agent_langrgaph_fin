#!/usr/bin/env python3
"""
Smart Document Chunker - Production Ready
Configurable chunking system with automatic level detection based on document size.

Usage:
    python smart_document_chunker.py <doc_name> [--level <none|section|subsection>] [--output-dir <dir>]

Automatic sizing rules:
    - < 2K chars: no chunking (return whole document)
    - ≤ 30K chars: section level chunking (1.1-1.10 + annexes)
    - > 30K chars: subsection level chunking (includes 1.1.1, 1.2.1, etc.)
"""

import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

sys.path.append('.')
from tools.document_tools import document_chunk_store

class SmartDocumentChunker:
    """Production-ready configurable document chunker."""
    
    def __init__(self):
        # Size thresholds for automatic level detection
        self.SIZE_THRESHOLDS = {
            'no_chunk': 2000,      # < 2K chars
            'section': 30000,      # ≤ 30K chars  
            'subsection': float('inf')  # > 30K chars
        }
        
        # Target sections for main document structure (12 chunks total)
        self.MAIN_SECTIONS = [
            {"section": "1.1", "title": "Scope of Application"},
            {"section": "1.2", "title": "Regulatory Capital"},
            {"section": "1.3", "title": "Total Risk weighted Assets"},
            {"section": "1.4", "title": "Approval to use Internal Model Based Approaches"},
            {"section": "1.5", "title": "Capital Floor–Internal Model Based Approaches"},
            {"section": "1.6", "title": "Calculation of OSFI Minimum Capital Requirements"},
            {"section": "1.7", "title": "Mandated Capital Buffers"},
            {"section": "1.8", "title": "Domestic Systemically Important Bank (D-SIB) Surcharge"},
            {"section": "1.9", "title": "Domestic Stability Buffer"},
            {"section": "1.10", "title": "Capital Targets"},
            {"section": "Annex 1", "title": "Domestic Systemic Importance and Capital Targets"},
            {"section": "Annex 2", "title": "Supervisory Target Capital Requirements"}
        ]
        
        # All subsections for detailed chunking
        self.ALL_SECTIONS = self.MAIN_SECTIONS + [
            {"section": "1.3.1", "title": "Credit Risk"},
            {"section": "1.3.2", "title": "Market Risk"},
            {"section": "1.3.3", "title": "Operational Risk"},
            {"section": "1.4.1", "title": "Approval to use the IRB Approaches to Credit Risk"},
            {"section": "1.5.1", "title": "The Capital Floor"},
            {"section": "1.5.2", "title": "Adjusted Capital Requirement"},
            {"section": "1.6.1", "title": "Risk-Based Capital Ratios for D-SIBs and Category I and II SMSBs"},
            {"section": "1.6.2", "title": "Simplified Risk-Based Capital Ratio for Category III SMSBs"},
            {"section": "1.7.1", "title": "Capital Conservation Buffer"},
            {"section": "1.7.2", "title": "Countercyclical Buffer"}
        ]
    
    def analyze_document(self, doc_name: str) -> Dict:
        """Analyze document and determine optimal chunking strategy."""
        
        if doc_name not in document_chunk_store:
            return {"error": f"Document '{doc_name}' not found in store"}
        
        chunks = document_chunk_store[doc_name]
        
        # Reconstruct full document
        full_text = ""
        for chunk in chunks:
            full_text += chunk.get('page_content', '') + "\n"
        
        char_count = len(full_text)
        word_count = len(full_text.split())
        
        # Determine optimal chunking level
        optimal_level = self._determine_optimal_level(char_count)
        
        return {
            'document_name': doc_name,
            'analysis': {
                'char_count': char_count,
                'word_count': word_count,
                'optimal_level': optimal_level,
                'main_sections_available': len(self.MAIN_SECTIONS),
                'all_sections_available': len(self.ALL_SECTIONS)
            },
            'recommendation': {
                'chunking_level': optimal_level,
                'rationale': self._get_level_rationale(char_count, optimal_level),
                'estimated_chunks': self._estimate_chunk_count(optimal_level)
            }
        }
    
    def chunk_document(self, doc_name: str, level: Optional[str] = None, output_dir: str = "output") -> Dict:
        """Chunk document with specified or auto-detected level."""
        
        # Analyze document first
        analysis = self.analyze_document(doc_name)
        if "error" in analysis:
            return analysis
        
        # Use specified level or auto-detected
        chunking_level = level or analysis['recommendation']['chunking_level']
        
        print(f"🔍 Chunking '{doc_name}' with level: {chunking_level}")
        print(f"📊 Document: {analysis['analysis']['char_count']:,} chars, {analysis['analysis']['word_count']:,} words")
        
        # Perform chunking based on level
        if chunking_level == 'none':
            result = self._create_no_chunks(doc_name, analysis)
        elif chunking_level == 'section':
            result = self._create_section_chunks(doc_name)
        elif chunking_level == 'subsection':
            result = self._create_subsection_chunks(doc_name)
        else:
            return {"error": f"Invalid chunking level: {chunking_level}"}
        
        # Create index
        index = self._create_document_index(result['chunks'], doc_name)
        
        # Save outputs
        output_files = self._save_outputs(result, index, output_dir)
        
        return {
            **result,
            'index': index,
            'output_files': output_files,
            'chunking_strategy': chunking_level,
            'analysis': analysis['analysis']
        }
    
    def _determine_optimal_level(self, char_count: int) -> str:
        """Determine optimal chunking level based on document size."""
        
        if char_count < self.SIZE_THRESHOLDS['no_chunk']:
            return 'none'
        elif char_count <= self.SIZE_THRESHOLDS['section']:
            return 'section'
        else:
            return 'subsection'
    
    def _get_level_rationale(self, char_count: int, level: str) -> str:
        """Get human-readable rationale for chunking level."""
        
        size_kb = char_count / 1000
        
        if level == 'none':
            return f"Small document ({size_kb:.1f}K chars) - no chunking needed"
        elif level == 'section':
            return f"Medium document ({size_kb:.1f}K chars) - section-level chunking (12 main sections)"
        else:
            return f"Large document ({size_kb:.1f}K chars) - subsection-level chunking (~22 sections)"
    
    def _estimate_chunk_count(self, level: str) -> int:
        """Estimate number of chunks for a given level."""
        
        if level == 'none':
            return 1
        elif level == 'section':
            return len(self.MAIN_SECTIONS)  # 12 chunks
        else:  # subsection
            return len(self.ALL_SECTIONS)   # 22 chunks
    
    def _create_no_chunks(self, doc_name: str, analysis: Dict) -> Dict:
        """Create single chunk for small documents."""
        
        chunks = document_chunk_store[doc_name]
        full_content = "\n".join(chunk.get('page_content', '') for chunk in chunks)
        
        return {
            'document': doc_name,
            'chunking_level': 'none',
            'total_chunks': 1,
            'chunks': [{
                'chunk_index': 0,
                'section_number': 'FULL_DOCUMENT',
                'title': f"Complete Document: {doc_name}",
                'content': full_content,
                'word_count': len(full_content.split()),
                'char_count': len(full_content),
                'metadata': {
                    'source': doc_name,
                    'chunk_type': 'full_document',
                    'is_complete': True
                }
            }]
        }
    
    def _create_section_chunks(self, doc_name: str) -> Dict:
        """Create main section chunks (1.1-1.10 + 2 annexes = 12 total)."""
        
        chunks = document_chunk_store[doc_name]
        full_text = "\n".join(chunk.get('page_content', '') for chunk in chunks)
        
        result_chunks = []
        
        for section_info in self.MAIN_SECTIONS:
            section_number = section_info['section']
            expected_title = section_info['title']
            
            print(f"   🔍 Extracting {section_number}: {expected_title}")
            
            # Extract content for this section using smart strategy
            content = self._extract_section_content_smart(full_text, section_number, expected_title)
            word_count = len(content.split()) if content else 0
            
            if word_count > 0:
                result_chunks.append({
                    'chunk_index': len(result_chunks),
                    'section_number': section_number,
                    'title': expected_title,
                    'content': content,
                    'word_count': word_count,
                    'char_count': len(content),
                    'metadata': {
                        'source': doc_name,
                        'chunk_type': 'main_section',
                        'hierarchy': self._parse_hierarchy(section_number)
                    }
                })
                print(f"      ✅ Found {word_count} words")
            else:
                print(f"      ❌ No content found")
        
        return {
            'document': doc_name,
            'chunking_level': 'section',
            'total_chunks': len(result_chunks),
            'chunks': result_chunks
        }
    
    def _create_subsection_chunks(self, doc_name: str) -> Dict:
        """Create detailed chunks including subsections (~22 total)."""
        
        chunks = document_chunk_store[doc_name]
        full_text = "\n".join(chunk.get('page_content', '') for chunk in chunks)
        
        result_chunks = []
        
        for section_info in self.ALL_SECTIONS:
            section_number = section_info['section']
            expected_title = section_info['title']
            
            print(f"   🔍 Extracting {section_number}: {expected_title}")
            
            content = self._extract_section_content_smart(full_text, section_number, expected_title)
            word_count = len(content.split()) if content else 0
            
            if word_count > 0:
                result_chunks.append({
                    'chunk_index': len(result_chunks),
                    'section_number': section_number,
                    'title': expected_title,
                    'content': content,
                    'word_count': word_count,
                    'char_count': len(content),
                    'metadata': {
                        'source': doc_name,
                        'chunk_type': 'detailed_section',
                        'hierarchy': self._parse_hierarchy(section_number)
                    }
                })
                print(f"      ✅ Found {word_count} words")
            else:
                print(f"      ❌ No content found")
        
        return {
            'document': doc_name,
            'chunking_level': 'subsection',
            'total_chunks': len(result_chunks),
            'chunks': result_chunks
        }
    
    def _extract_section_content_smart(self, full_text: str, section_number: str, expected_title: str) -> str:
        """Smart content extraction using multiple strategies."""
        
        lines = full_text.split('\n')
        
        # Strategy 1: Find by page boundaries + content analysis
        page_content = self._extract_by_page_analysis(lines, section_number, expected_title)
        if len(page_content.split()) > 100:
            return page_content
        
        # Strategy 2: Find by keyword matching
        keyword_content = self._extract_by_keywords(lines, expected_title)
        if len(keyword_content.split()) > 100:
            return keyword_content
        
        # Strategy 3: Find by section patterns in text
        pattern_content = self._extract_by_patterns(lines, section_number)
        if len(pattern_content.split()) > 50:
            return pattern_content
        
        # Strategy 4: Broad content extraction based on position estimation
        estimated_content = self._extract_by_position_estimation(lines, section_number)
        
        return estimated_content
    
    def _extract_by_page_analysis(self, lines: List[str], section_number: str, expected_title: str) -> str:
        """Extract content by analyzing page boundaries."""
        
        # Map section to expected page ranges (based on TOC)
        page_mapping = {
            '1.1': (4, 4), '1.2': (4, 5), '1.3': (5, 7), '1.4': (8, 8), '1.5': (9, 11),
            '1.6': (11, 12), '1.7': (12, 18), '1.8': (18, 19), '1.9': (19, 20), '1.10': (20, 22),
            'Annex 1': (22, 26), 'Annex 2': (26, 30)
        }
        
        if section_number not in page_mapping:
            return ""
        
        start_page, end_page = page_mapping[section_number]
        
        # Find page boundaries
        page_boundaries = {}
        for line_num, line in enumerate(lines):
            if re.match(r'^##\s*Page\s+(\d+)', line.strip()):
                page_match = re.match(r'^##\s*Page\s+(\d+)', line.strip())
                if page_match:
                    page_num = int(page_match.group(1))
                    page_boundaries[page_num] = line_num
        
        # Extract content from page range
        start_line = page_boundaries.get(start_page, 0)
        end_line = page_boundaries.get(end_page + 1, len(lines))
        
        if start_line < end_line:
            content_lines = lines[start_line:end_line]
            return '\n'.join(content_lines).strip()
        
        return ""
    
    def _extract_by_keywords(self, lines: List[str], expected_title: str) -> str:
        """Extract content by searching for title keywords."""
        
        # Extract key terms from title
        keywords = self._extract_title_keywords(expected_title)
        
        best_start = None
        best_score = 0
        
        # Find line with best keyword match
        for line_num, line in enumerate(lines):
            line_lower = line.strip().lower()
            score = sum(1 for keyword in keywords if keyword in line_lower)
            
            if score > best_score:
                best_score = score
                best_start = line_num
        
        if best_start is not None and best_score >= 2:
            # Extract content around this area
            start_line = max(0, best_start - 5)
            end_line = min(len(lines), best_start + 150)
            
            content_lines = lines[start_line:end_line]
            return '\n'.join(content_lines).strip()
        
        return ""
    
    def _extract_by_patterns(self, lines: List[str], section_number: str) -> str:
        """Extract content by finding section number patterns."""
        
        patterns = [
            rf'^{re.escape(section_number)}\.?\s+(.+)$',
            rf'{re.escape(section_number)}\s+(.+)$',
            rf'{re.escape(section_number)}\.(.+)$'
        ]
        
        for line_num, line in enumerate(lines):
            line_clean = line.strip()
            
            for pattern in patterns:
                if re.match(pattern, line_clean):
                    # Extract content from this point
                    start_line = line_num
                    end_line = min(len(lines), start_line + 100)
                    
                    content_lines = lines[start_line:end_line]
                    return '\n'.join(content_lines).strip()
        
        return ""
    
    def _extract_by_position_estimation(self, lines: List[str], section_number: str) -> str:
        """Extract content by estimating position in document."""
        
        # Simple position-based extraction
        total_lines = len(lines)
        
        # Estimate position based on section number
        if section_number.startswith('1.1'):
            start_ratio = 0.05
        elif section_number.startswith('1.2'):
            start_ratio = 0.1
        elif section_number.startswith('1.3'):
            start_ratio = 0.15
        elif section_number.startswith('1.4'):
            start_ratio = 0.25
        elif section_number.startswith('1.5'):
            start_ratio = 0.35
        elif section_number.startswith('1.6'):
            start_ratio = 0.45
        elif section_number.startswith('1.7'):
            start_ratio = 0.55
        elif section_number.startswith('1.8'):
            start_ratio = 0.7
        elif section_number.startswith('1.9'):
            start_ratio = 0.8
        elif section_number.startswith('1.10'):
            start_ratio = 0.85
        elif 'Annex 1' in section_number:
            start_ratio = 0.9
        elif 'Annex 2' in section_number:
            start_ratio = 0.95
        else:
            start_ratio = 0.5
        
        start_line = int(total_lines * start_ratio)
        end_line = min(total_lines, start_line + 150)
        
        content_lines = lines[start_line:end_line]
        return '\n'.join(content_lines).strip()
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from titles."""
        
        stop_words = {'the', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'a', 'an', 'use', 'based', 'requirements'}
        words = re.findall(r'\b\w+\b', title.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        return keywords[:3]  # Top 3 keywords
    
    def _parse_hierarchy(self, section_number: str) -> Dict:
        """Parse section hierarchy."""
        
        if section_number.startswith('Annex') or section_number == 'FULL_DOCUMENT':
            return {
                'section': section_number,
                'subsection': None,
                'sub_subsection': None
            }
        
        parts = section_number.split('.')
        return {
            'section': parts[0] if len(parts) >= 1 else None,
            'subsection': f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else None,
            'sub_subsection': f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else None
        }
    
    def _create_document_index(self, chunks: List[Dict], doc_name: str) -> Dict:
        """Create clean document index with only essential mappings."""
        
        index = {
            'document_name': doc_name,
            'total_chunks': len(chunks),
            'created_at': datetime.now().isoformat(),
            'section_map': {},
            'quick_lookup': {}
        }
        
        for chunk in chunks:
            section_num = chunk['section_number']
            title = chunk['title']
            hierarchy = chunk['metadata']['hierarchy']
            
            # Section mapping
            index['section_map'][section_num] = {
                'chunk_id': chunk['chunk_index'],
                'title': title,
                'word_count': chunk['word_count'],
                'section': hierarchy['section'],
                'subsection': hierarchy['subsection'],
                'sub_subsection': hierarchy['sub_subsection']
            }
            
            # Quick lookup
            index['quick_lookup'][section_num] = chunk['chunk_index']
        
        return index
    
    def _save_outputs(self, result: Dict, index: Dict, output_dir: str) -> Dict:
        """Save chunks and index to files."""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        doc_name = result['document'].replace('.pdf', '').replace('8726afa4-554d-42b9-b257-3d06e663b941_', '').replace('/', '_')
        
        # Simple file names
        chunks_file = output_path / f"{doc_name}_chunks.json"
        index_file = output_path / f"{doc_name}_index.json"
        
        # Save chunks
        with open(chunks_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save index
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        return {
            'chunks_file': str(chunks_file),
            'index_file': str(index_file)
        }

def main():
    """Command line interface for the smart chunker."""
    
    parser = argparse.ArgumentParser(description='Smart Document Chunker')
    parser.add_argument('doc_name', help='Document name to chunk')
    parser.add_argument('--level', choices=['none', 'section', 'subsection'], 
                       help='Chunking level (auto-detected if not specified)')
    parser.add_argument('--output-dir', default='output', 
                       help='Output directory (default: output)')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze document, do not chunk')
    
    args = parser.parse_args()
    
    chunker = SmartDocumentChunker()
    
    print("🤖 Smart Document Chunker - Production Ready")
    print("=" * 60)
    
    if args.analyze_only:
        # Analyze only
        result = chunker.analyze_document(args.doc_name)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"📊 Analysis Results:")
        print(f"   Document: {result['document_name']}")
        print(f"   Size: {result['analysis']['char_count']:,} chars, {result['analysis']['word_count']:,} words")
        print(f"   Recommended level: {result['recommendation']['chunking_level']}")
        print(f"   Rationale: {result['recommendation']['rationale']}")
        print(f"   Estimated chunks: {result['recommendation']['estimated_chunks']}")
    else:
        # Full chunking
        result = chunker.chunk_document(args.doc_name, args.level, args.output_dir)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"\n✅ Chunking completed successfully!")
        print(f"   Strategy: {result['chunking_strategy']}")
        print(f"   Total chunks: {result['total_chunks']}")
        print(f"   Total words: {sum(c['word_count'] for c in result['chunks']):,}")
        
        print(f"\n📋 All chunks created:")
        for i, chunk in enumerate(result['chunks']):
            print(f"   {i+1:2d}. {chunk['section_number']:8s} - {chunk['title'][:50]:<50} ({chunk['word_count']:,} words)")
        
        print(f"\n📁 Output files:")
        print(f"     📦 Chunks: {result['output_files']['chunks_file']}")
        print(f"     🗂️ Index: {result['output_files']['index_file']}")

if __name__ == "__main__":
    main()