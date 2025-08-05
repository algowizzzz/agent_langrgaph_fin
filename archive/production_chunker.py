#!/usr/bin/env python3
"""
Production-Ready Document Chunker
Uses pre-extracted text for reliable, configurable chunking.

Features:
- Automatic level detection based on document size
- Clean section extraction using structured text
- Produces exactly 12 main sections or 22+ detailed sections
- Creates index files for fast search
"""

import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import fitz  # PyMuPDF

class ProductionChunker:
    """Production-ready configurable document chunker."""
    
    def __init__(self):
        # Size thresholds for automatic level detection
        self.SIZE_THRESHOLDS = {
            'no_chunk': 2000,      # < 2K chars
            'section': 30000,      # ≤ 30K chars  
            'subsection': float('inf')  # > 30K chars
        }
        
        # Target main sections (12 chunks)
        self.MAIN_SECTIONS = [
            "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", 
            "1.7", "1.8", "1.9", "1.10", "Annex 1", "Annex 2"
        ]
        
        # All sections for detailed chunking
        self.ALL_SECTIONS = self.MAIN_SECTIONS + [
            "1.3.1", "1.3.2", "1.3.3", "1.4.1", "1.5.1", "1.5.2",
            "1.6.1", "1.6.2", "1.7.1", "1.7.2"
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract clean text from PDF using PyMuPDF."""
        
        try:
            doc = fitz.open(pdf_path)
            
            all_text = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                all_text += f"\n\n=== PAGE {page_num + 1} ===\n\n"
                all_text += page_text
            
            doc.close()
            
            print(f"✅ Extracted {len(all_text):,} characters from {page_count} pages")
            return all_text
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            return ""
    
    def load_existing_text(self, text_file: str) -> str:
        """Load text from existing file."""
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print(f"✅ Loaded {len(text):,} characters from {text_file}")
            return text
            
        except Exception as e:
            print(f"❌ Failed to load text file: {e}")
            return ""
    
    def analyze_document(self, input_source: str, is_text_file: bool = False) -> Dict:
        """Analyze document and determine optimal chunking strategy."""
        
        # Load text
        if is_text_file:
            full_text = self.load_existing_text(input_source)
            doc_name = Path(input_source).stem
        else:
            full_text = self.extract_text_from_pdf(input_source)
            doc_name = Path(input_source).name
        
        if not full_text:
            return {"error": "Failed to load text content"}
        
        char_count = len(full_text)
        word_count = len(full_text.split())
        
        # Determine optimal chunking level
        optimal_level = self._determine_optimal_level(char_count)
        
        # Detect available sections
        available_sections = self._detect_sections(full_text)
        
        return {
            'document_name': doc_name,
            'extracted_text': full_text,
            'analysis': {
                'char_count': char_count,
                'word_count': word_count,
                'optimal_level': optimal_level,
                'available_sections': len(available_sections),
                'section_list': [s['section_number'] for s in available_sections]
            },
            'recommendation': {
                'chunking_level': optimal_level,
                'rationale': self._get_level_rationale(char_count, optimal_level),
                'estimated_chunks': self._estimate_chunk_count(optimal_level)
            }
        }
    
    def chunk_document(self, input_source: str, level: Optional[str] = None, output_dir: str = "output", is_text_file: bool = False) -> Dict:
        """Chunk document with specified or auto-detected level."""
        
        # Analyze document first
        analysis = self.analyze_document(input_source, is_text_file)
        if "error" in analysis:
            return analysis
        
        # Use specified level or auto-detected
        chunking_level = level or analysis['recommendation']['chunking_level']
        full_text = analysis['extracted_text']
        doc_name = analysis['document_name']
        
        print(f"🔍 Chunking with level: {chunking_level}")
        print(f"📊 Document: {analysis['analysis']['char_count']:,} chars, {analysis['analysis']['word_count']:,} words")
        print(f"🎯 Available sections: {analysis['analysis']['available_sections']}")
        
        # Perform chunking based on level
        if chunking_level == 'none':
            result = self._create_no_chunks(doc_name, full_text)
        elif chunking_level == 'section':
            result = self._create_section_chunks(doc_name, full_text)
        elif chunking_level == 'subsection':
            result = self._create_subsection_chunks(doc_name, full_text)
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
            return len(self.ALL_SECTIONS)   # 22+ chunks
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """Detect all numbered sections and annexes in the text."""
        
        sections = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Look for numbered sections (1.1, 1.2.3, etc.)
            section_match = re.match(r'^(\d+(?:\.\d+)*)\.\s*(.*)$', line)
            if section_match:
                section_number = section_match.group(1)
                title = section_match.group(2).strip()
                
                sections.append({
                    'section_number': section_number,
                    'title': title,
                    'line_number': line_num,
                    'raw_line': line
                })
            
            # Look for Annex sections
            annex_match = re.match(r'^(Annex\s+\d+)\s*(.*)$', line)
            if annex_match:
                section_number = annex_match.group(1)
                title = annex_match.group(2).strip()
                
                sections.append({
                    'section_number': section_number,
                    'title': title,
                    'line_number': line_num,
                    'raw_line': line
                })
        
        return sections
    
    def _create_no_chunks(self, doc_name: str, full_text: str) -> Dict:
        """Create single chunk for small documents."""
        
        return {
            'document': doc_name,
            'chunking_level': 'none',
            'total_chunks': 1,
            'chunks': [{
                'chunk_index': 0,
                'section_number': 'FULL_DOCUMENT',
                'title': f"Complete Document: {doc_name}",
                'content': full_text,
                'word_count': len(full_text.split()),
                'char_count': len(full_text),
                'metadata': {
                    'source': doc_name,
                    'chunk_type': 'full_document',
                    'is_complete': True
                }
            }]
        }
    
    def _create_section_chunks(self, doc_name: str, full_text: str) -> Dict:
        """Create main section chunks (1.1-1.10 + 2 annexes = 12 total)."""
        
        lines = full_text.split('\n')
        result_chunks = []
        
        for target_section in self.MAIN_SECTIONS:
            print(f"   🔍 Extracting {target_section}")
            
            content = self._extract_section_content(lines, target_section)
            word_count = len(content.split()) if content else 0
            
            if word_count > 0:
                result_chunks.append({
                    'chunk_index': len(result_chunks),
                    'section_number': target_section,
                    'title': self._get_section_title(target_section),
                    'content': content,
                    'word_count': word_count,
                    'char_count': len(content),
                    'metadata': {
                        'source': doc_name,
                        'chunk_type': 'main_section',
                        'extraction_method': 'pymupdf',
                        'hierarchy': self._parse_hierarchy(target_section)
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
    
    def _create_subsection_chunks(self, doc_name: str, full_text: str) -> Dict:
        """Create detailed chunks including subsections."""
        
        lines = full_text.split('\n')
        result_chunks = []
        
        for target_section in self.ALL_SECTIONS:
            print(f"   🔍 Extracting {target_section}")
            
            content = self._extract_section_content(lines, target_section)
            word_count = len(content.split()) if content else 0
            
            if word_count > 0:
                result_chunks.append({
                    'chunk_index': len(result_chunks),
                    'section_number': target_section,
                    'title': self._get_section_title(target_section),
                    'content': content,
                    'word_count': word_count,
                    'char_count': len(content),
                    'metadata': {
                        'source': doc_name,
                        'chunk_type': 'detailed_section',
                        'extraction_method': 'pymupdf',
                        'hierarchy': self._parse_hierarchy(target_section)
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
    
    def _extract_section_content(self, lines: List[str], target_section: str) -> str:
        """Extract content for a specific section."""
        
        # Find the start of this section
        start_line = None
        
        # Look for section patterns
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            if target_section.startswith('Annex'):
                # Look for "Annex 1" or "Annex 2"
                if re.match(rf'^{re.escape(target_section)}\b', line):
                    start_line = line_num
                    break
            else:
                # Look for numbered sections like "1.1" or "1.3.2"
                patterns = [
                    rf'^{re.escape(target_section)}\.\s',      # "1.1. Title"
                    rf'^{re.escape(target_section)}\s',        # "1.1 Title"
                    rf'^{re.escape(target_section)}$'          # Just "1.1"
                ]
                
                for pattern in patterns:
                    if re.match(pattern, line):
                        start_line = line_num
                        break
                
                if start_line is not None:
                    break
        
        if start_line is None:
            return ""
        
        # Find the end of this section
        end_line = len(lines)
        
        # Look for the next main section
        next_main_sections = []
        current_index = self.MAIN_SECTIONS.index(target_section) if target_section in self.MAIN_SECTIONS else -1
        
        if current_index >= 0 and current_index < len(self.MAIN_SECTIONS) - 1:
            # Get the next main section
            next_main_sections.append(self.MAIN_SECTIONS[current_index + 1])
        
        # Also add other main sections as potential boundaries
        for section in self.MAIN_SECTIONS:
            if section != target_section:
                next_main_sections.append(section)
        
        # Look for section boundaries
        for line_num in range(start_line + 1, len(lines)):
            line = lines[line_num].strip()
            
            # Check for any of the next main sections
            for next_section in next_main_sections:
                if next_section.startswith('Annex'):
                    if re.match(rf'^{re.escape(next_section)}\b', line):
                        end_line = line_num
                        break
                else:
                    patterns = [
                        rf'^{re.escape(next_section)}\.\s',
                        rf'^{re.escape(next_section)}\s',
                        rf'^{re.escape(next_section)}$'
                    ]
                    
                    for pattern in patterns:
                        if re.match(pattern, line):
                            end_line = line_num
                            break
                
                if end_line < len(lines):
                    break
            
            if end_line < len(lines):
                break
            
            # Safety limit - don't extract more than 300 lines
            if line_num - start_line > 300:
                end_line = line_num
                break
        
        # Extract content
        content_lines = lines[start_line:end_line]
        content = '\n'.join(content_lines).strip()
        
        # Clean up content - remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    def _get_section_title(self, section_number: str) -> str:
        """Get descriptive title for a section."""
        
        titles = {
            "1.1": "Scope of Application",
            "1.2": "Regulatory Capital",
            "1.3": "Total Risk weighted Assets",
            "1.3.1": "Credit Risk",
            "1.3.2": "Market Risk", 
            "1.3.3": "Operational Risk",
            "1.4": "Approval to use Internal Model Based Approaches",
            "1.4.1": "Approval to use the IRB Approaches to Credit Risk",
            "1.5": "Capital Floor–Internal Model Based Approaches",
            "1.5.1": "The Capital Floor",
            "1.5.2": "Adjusted Capital Requirement",
            "1.6": "Calculation of OSFI Minimum Capital Requirements",
            "1.6.1": "Risk-Based Capital Ratios for D-SIBs and Category I and II SMSBs",
            "1.6.2": "Simplified Risk-Based Capital Ratio for Category III SMSBs",
            "1.7": "Mandated Capital Buffers",
            "1.7.1": "Capital Conservation Buffer",
            "1.7.2": "Countercyclical Buffer",
            "1.8": "Domestic Systemically Important Bank (D-SIB) Surcharge",
            "1.9": "Domestic Stability Buffer",
            "1.10": "Capital Targets",
            "Annex 1": "Domestic Systemic Importance and Capital Targets",
            "Annex 2": "Supervisory Target Capital Requirements"
        }
        
        return titles.get(section_number, section_number)
    
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
        
        doc_name = result['document'].replace('.pdf', '').replace('8726afa4-554d-42b9-b257-3d06e663b941_', '')
        
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
    """Command line interface for the production chunker."""
    
    parser = argparse.ArgumentParser(description='Production Document Chunker')
    parser.add_argument('input_path', help='Path to PDF file or extracted text file to chunk')
    parser.add_argument('--level', choices=['none', 'section', 'subsection'], 
                       help='Chunking level (auto-detected if not specified)')
    parser.add_argument('--output-dir', default='output', 
                       help='Output directory (default: output)')
    parser.add_argument('--text-file', action='store_true',
                       help='Input is a text file instead of PDF')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze document, do not chunk')
    
    args = parser.parse_args()
    
    chunker = ProductionChunker()
    
    print("🚀 Production Document Chunker")
    print("=" * 60)
    
    if args.analyze_only:
        # Analyze only
        result = chunker.analyze_document(args.input_path, args.text_file)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"📊 Analysis Results:")
        print(f"   Document: {result['document_name']}")
        print(f"   Size: {result['analysis']['char_count']:,} chars, {result['analysis']['word_count']:,} words")
        print(f"   Available sections: {result['analysis']['available_sections']}")
        print(f"   Recommended level: {result['recommendation']['chunking_level']}")
        print(f"   Rationale: {result['recommendation']['rationale']}")
        print(f"   Estimated chunks: {result['recommendation']['estimated_chunks']}")
        
        print(f"\n🔍 Detected sections:")
        for section in result['analysis']['section_list'][:10]:
            print(f"   - {section}")
        if len(result['analysis']['section_list']) > 10:
            print(f"   ... and {len(result['analysis']['section_list']) - 10} more")
    else:
        # Full chunking
        result = chunker.chunk_document(args.input_path, args.level, args.output_dir, args.text_file)
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