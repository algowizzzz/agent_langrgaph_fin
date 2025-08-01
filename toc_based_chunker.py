#!/usr/bin/env python3
"""
Table of Contents-Based Document Chunker
Analyzes document structure using numbered sections (1.1, 1.2, 1.3.1, etc.)
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

sys.path.append('.')
from tools.document_tools import document_chunk_store

class TOCBasedChunker:
    """Creates semantic chunks based on Table of Contents structure."""
    
    def __init__(self):
        # Patterns for different section numbering levels
        self.section_patterns = {
            1: r'^(\d+)\.\s+(.+)$',                    # 1. Section
            2: r'^(\d+\.\d+)\s+(.+)$',                 # 1.1 Subsection  
            3: r'^(\d+\.\d+\.\d+)\s+(.+)$',           # 1.1.1 Sub-subsection
            4: r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$',     # 1.1.1.1 Sub-sub-subsection
        }
        
        # Also detect Annex patterns
        self.annex_pattern = r'^(Annex\s+\d+)\s+(.+)$'
        
    def extract_toc_structure(self, doc_name: str) -> Dict:
        """Extract numbered sections from document content."""
        
        if doc_name not in document_chunk_store:
            return {"error": f"Document {doc_name} not found"}
            
        chunks = document_chunk_store[doc_name]
        
        # Reconstruct full document text
        full_text = ""
        for chunk in chunks:
            full_text += chunk.get('page_content', '') + "\n"
        
        print(f"🔍 Analyzing TOC structure for: {doc_name}")
        print(f"📊 Total document length: {len(full_text)} characters")
        
        # Find all numbered sections
        sections = []
        lines = full_text.split('\n')
        
        current_section_content = []
        current_section = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                current_section_content.append("")
                continue
            
            # Check for numbered sections
            section_found = False
            
            # Check main patterns (1.1, 1.2.3, etc.)
            for level, pattern in self.section_patterns.items():
                match = re.match(pattern, line)
                if match:
                    # Save previous section
                    if current_section:
                        word_count = len(' '.join(current_section_content).split())
                        current_section['word_count'] = word_count
                        current_section['content'] = '\n'.join(current_section_content)
                        sections.append(current_section)
                    
                    # Start new section
                    section_number = match.group(1)
                    section_title = match.group(2).strip()
                    
                    current_section = {
                        'section_number': section_number,
                        'title': section_title,
                        'level': level,
                        'line_number': line_num,
                        'raw_line': line,
                        'hierarchy': self._parse_hierarchy(section_number)
                    }
                    current_section_content = []
                    section_found = True
                    break
            
            # Check for Annex pattern
            if not section_found:
                annex_match = re.match(self.annex_pattern, line)
                if annex_match:
                    # Save previous section
                    if current_section:
                        word_count = len(' '.join(current_section_content).split())
                        current_section['word_count'] = word_count
                        current_section['content'] = '\n'.join(current_section_content)
                        sections.append(current_section)
                    
                    # Start new annex
                    annex_number = annex_match.group(1)
                    annex_title = annex_match.group(2).strip()
                    
                    current_section = {
                        'section_number': annex_number,
                        'title': annex_title,
                        'level': 1,  # Treat as top level
                        'line_number': line_num,
                        'raw_line': line,
                        'hierarchy': {'section': annex_number, 'subsection': None, 'sub_subsection': None}
                    }
                    current_section_content = []
                    section_found = True
            
            if not section_found:
                current_section_content.append(line)
        
        # Don't forget the last section
        if current_section:
            word_count = len(' '.join(current_section_content).split())
            current_section['word_count'] = word_count
            current_section['content'] = '\n'.join(current_section_content)
            sections.append(current_section)
        
        return {
            "document": doc_name,
            "total_chars": len(full_text),
            "sections": sections,
            "structure_analysis": self._analyze_toc_structure(sections)
        }
    
    def _parse_hierarchy(self, section_number: str) -> Dict:
        """Parse section number into hierarchy (1.2.3 -> section=1, subsection=2, sub_subsection=3)."""
        
        parts = section_number.split('.')
        hierarchy = {
            'section': None,
            'subsection': None, 
            'sub_subsection': None,
            'sub_sub_subsection': None
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
    
    def _analyze_toc_structure(self, sections: List[Dict]) -> Dict:
        """Analyze the table of contents structure."""
        
        level_stats = defaultdict(list)
        section_distribution = defaultdict(int)
        
        for section in sections:
            level = section['level']
            word_count = section.get('word_count', 0)
            section_num = section['section_number']
            
            level_stats[level].append(word_count)
            
            # Count sections by main number (1.x.x -> 1)
            if '.' in section_num:
                main_section = section_num.split('.')[0]
                section_distribution[main_section] += 1
        
        analysis = {
            'total_sections': len(sections),
            'level_distribution': dict(section_distribution),
            'level_stats': {}
        }
        
        for level, word_counts in level_stats.items():
            if word_counts:
                analysis['level_stats'][f"level_{level}"] = {
                    "count": len(word_counts),
                    "avg_words": sum(word_counts) / len(word_counts),
                    "min_words": min(word_counts),
                    "max_words": max(word_counts),
                    "total_words": sum(word_counts)
                }
        
        # Recommend chunking strategy
        analysis["recommendation"] = self._recommend_toc_chunking(analysis, sections)
        
        return analysis
    
    def _recommend_toc_chunking(self, analysis: Dict, sections: List[Dict]) -> Dict:
        """Recommend optimal chunking based on TOC structure."""
        
        level_stats = analysis.get('level_stats', {})
        
        recommendations = []
        
        # Option 1: Level 2 sections (1.1, 1.2, etc.)
        if 'level_2' in level_stats:
            stats = level_stats['level_2']
            avg_words = stats['avg_words']
            count = stats['count']
            
            if 200 <= avg_words <= 1000:
                score = 90
                rationale = f"Perfect: {count} level-2 sections, {avg_words:.0f} avg words"
            else:
                score = 70
                rationale = f"Good: {count} level-2 sections, {avg_words:.0f} avg words"
                
            recommendations.append({
                'strategy': 'level_2_sections',
                'level': 2,
                'score': score,
                'chunk_count': count,
                'avg_words': avg_words,
                'rationale': rationale
            })
        
        # Option 2: Level 3 sections (1.1.1, 1.2.3, etc.)  
        if 'level_3' in level_stats:
            stats = level_stats['level_3']
            avg_words = stats['avg_words']
            count = stats['count']
            
            if 100 <= avg_words <= 600:
                score = 85
                rationale = f"Detailed: {count} level-3 sections, {avg_words:.0f} avg words"
            else:
                score = 60
                rationale = f"Too granular: {count} level-3 sections, {avg_words:.0f} avg words"
                
            recommendations.append({
                'strategy': 'level_3_sections',
                'level': 3,
                'score': score,
                'chunk_count': count,
                'avg_words': avg_words,
                'rationale': rationale
            })
        
        # Option 3: Mixed strategy (group small subsections)
        mixed_chunks = self._estimate_mixed_strategy(sections)
        recommendations.append({
            'strategy': 'mixed_grouping',
            'level': 'mixed',
            'score': 75,
            'chunk_count': len(mixed_chunks),
            'avg_words': sum(c['word_count'] for c in mixed_chunks) / len(mixed_chunks) if mixed_chunks else 0,
            'rationale': f"Smart grouping: {len(mixed_chunks)} logical chunks"
        })
        
        # Select best recommendation
        if recommendations:
            best = max(recommendations, key=lambda x: x['score'])
            return {
                'recommended_strategy': best['strategy'],
                'recommended_level': best['level'],
                'confidence': best['score'],
                'rationale': best['rationale'],
                'estimated_chunks': best['chunk_count'],
                'all_options': sorted(recommendations, key=lambda x: x['score'], reverse=True)
            }
        else:
            return {
                'recommended_strategy': 'level_2_sections',
                'recommended_level': 2,
                'confidence': 50,
                'rationale': 'Default to level 2 sections',
                'estimated_chunks': len([s for s in sections if s['level'] == 2]),
                'all_options': []
            }
    
    def _estimate_mixed_strategy(self, sections: List[Dict]) -> List[Dict]:
        """Estimate chunks using mixed strategy (group small sections)."""
        
        chunks = []
        current_chunk = None
        
        for section in sections:
            word_count = section.get('word_count', 0)
            
            # If it's a substantial section (>300 words), make it its own chunk
            if word_count >= 300:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = None
                
                chunks.append({
                    'sections': [section],
                    'word_count': word_count,
                    'type': 'single_section'
                })
            
            # If it's a small section, group with others
            else:
                if not current_chunk:
                    current_chunk = {
                        'sections': [section],
                        'word_count': word_count,
                        'type': 'grouped_sections'
                    }
                else:
                    current_chunk['sections'].append(section)
                    current_chunk['word_count'] += word_count
                    
                    # If grouped chunk gets too big, finalize it
                    if current_chunk['word_count'] >= 800:
                        chunks.append(current_chunk)
                        current_chunk = None
        
        # Don't forget remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def create_toc_based_chunks(self, doc_name: str, strategy: str = "recommended") -> Dict:
        """Create chunks based on table of contents structure."""
        
        structure = self.extract_toc_structure(doc_name)
        if "error" in structure:
            return structure
        
        sections = structure["sections"]
        analysis = structure["structure_analysis"]
        
        if strategy == "recommended":
            strategy = analysis["recommendation"]["recommended_strategy"]
        
        print(f"🎯 Using chunking strategy: {strategy}")
        
        if strategy == "level_2_sections":
            chunks = self._create_level_based_chunks(sections, target_level=2)
        elif strategy == "level_3_sections":
            chunks = self._create_level_based_chunks(sections, target_level=3)
        elif strategy == "mixed_grouping":
            chunks = self._create_mixed_chunks(sections)
        else:
            # Default to level 2
            chunks = self._create_level_based_chunks(sections, target_level=2)
        
        return {
            'document': doc_name,
            'chunking_strategy': strategy,
            'total_chunks': len(chunks),
            'chunks': chunks,
            'index': self._create_toc_index(chunks),
            'toc_structure': structure
        }
    
    def _create_level_based_chunks(self, sections: List[Dict], target_level: int) -> List[Dict]:
        """Create chunks based on specific hierarchy level."""
        
        chunks = []
        current_chunk = None
        
        for section in sections:
            # If this is a target level section, start new chunk
            if section['level'] == target_level:
                if current_chunk:
                    chunks.append(current_chunk)
                
                current_chunk = {
                    'chunk_index': len(chunks),
                    'primary_section': section,
                    'sections': [section],
                    'section_number': section['section_number'],
                    'title': section['title'],
                    'content': section['raw_line'] + '\n' + section['content'],
                    'word_count': section['word_count'],
                    'hierarchy': section['hierarchy'],
                    'chunk_type': f'level_{target_level}_section',
                    'metadata': {
                        'source': sections[0].get('source', 'unknown'),
                        'file_type': 'PDF',
                        'chunk_type': 'toc_based',
                        'chunking_level': target_level,
                        'section_hierarchy': section['hierarchy']
                    }
                }
            
            # If this is a deeper level, add to current chunk
            elif section['level'] > target_level and current_chunk:
                current_chunk['sections'].append(section)
                current_chunk['content'] += '\n' + section['raw_line'] + '\n' + section['content']
                current_chunk['word_count'] += section['word_count']
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _create_mixed_chunks(self, sections: List[Dict]) -> List[Dict]:
        """Create chunks using mixed strategy."""
        
        mixed_groups = self._estimate_mixed_strategy(sections)
        chunks = []
        
        for i, group in enumerate(mixed_groups):
            group_sections = group['sections']
            primary_section = group_sections[0]
            
            # Combine content from all sections in group
            content_parts = []
            total_word_count = 0
            
            for section in group_sections:
                content_parts.append(section['raw_line'] + '\n' + section['content'])
                total_word_count += section['word_count']
            
            chunk = {
                'chunk_index': i,
                'primary_section': primary_section,
                'sections': group_sections,
                'section_number': primary_section['section_number'],
                'title': primary_section['title'],
                'content': '\n'.join(content_parts),
                'word_count': total_word_count,
                'hierarchy': primary_section['hierarchy'],
                'chunk_type': group['type'],
                'metadata': {
                    'source': 'unknown',
                    'file_type': 'PDF',
                    'chunk_type': 'toc_mixed',
                    'section_count': len(group_sections),
                    'section_hierarchy': primary_section['hierarchy']
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_toc_index(self, chunks: List[Dict]) -> Dict:
        """Create searchable index for TOC-based chunks."""
        
        index = {
            'by_section_number': {},
            'by_hierarchy': defaultdict(list),
            'by_title_keywords': defaultdict(list),
            'chunk_summary': []
        }
        
        for chunk in chunks:
            chunk_id = chunk['chunk_index']
            section_number = chunk['section_number']
            title = chunk['title']
            hierarchy = chunk['hierarchy']
            
            # Index by section number
            index['by_section_number'][section_number] = chunk_id
            
            # Index by hierarchy levels
            if hierarchy['section']:
                index['by_hierarchy'][f"section_{hierarchy['section']}"].append(chunk_id)
            if hierarchy['subsection']:
                index['by_hierarchy'][f"subsection_{hierarchy['subsection']}"].append(chunk_id)
            if hierarchy['sub_subsection']:
                index['by_hierarchy'][f"sub_subsection_{hierarchy['sub_subsection']}"].append(chunk_id)
            
            # Index by title keywords
            title_words = title.lower().split()
            for word in title_words:
                if len(word) > 3:  # Skip short words
                    index['by_title_keywords'][word].append(chunk_id)
            
            # Create summary
            index['chunk_summary'].append({
                'chunk_id': chunk_id,
                'section_number': section_number,
                'title': title,
                'word_count': chunk['word_count'],
                'hierarchy_path': f"{hierarchy['section']} > {hierarchy['subsection']} > {hierarchy['sub_subsection']}".replace(' > None', '')
            })
        
        return index

def main():
    """Analyze document using Table of Contents structure."""
    
    chunker = TOCBasedChunker()
    
    # Target document
    doc_name = "8726afa4-554d-42b9-b257-3d06e663b941_car24_chpt1_0.pdf"
    
    print("🔍 STEP 1: Extracting Table of Contents Structure")
    print("=" * 60)
    
    structure = chunker.extract_toc_structure(doc_name)
    
    if "error" in structure:
        print(f"❌ {structure['error']}")
        return
    
    sections = structure['sections']
    analysis = structure['structure_analysis']
    
    print(f"📊 TOC Structure Analysis:")
    print(f"   📄 Document: {structure['document']}")
    print(f"   📏 Total chars: {structure['total_chars']:,}")
    print(f"   📋 Sections found: {len(sections)}")
    
    # Show section distribution
    print(f"\n📈 Section Level Distribution:")
    for level_key, stats in analysis['level_stats'].items():
        level = level_key.split("_")[1]
        print(f"   Level {level}: {stats['count']} sections, avg {stats['avg_words']:.0f} words")
    
    # Show first few sections
    print(f"\n🔍 First 10 Sections:")
    for i, section in enumerate(sections[:10]):
        print(f"   {section['section_number']}: {section['title']} ({section.get('word_count', 0)} words)")
    
    # Show recommendation
    rec = analysis['recommendation']
    print(f"\n🎯 Chunking Recommendation:")
    print(f"   📌 Strategy: {rec['recommended_strategy']}")
    print(f"   🎯 Confidence: {rec['confidence']}/100")
    print(f"   💡 Rationale: {rec['rationale']}")
    print(f"   📦 Est. chunks: {rec['estimated_chunks']}")
    
    print(f"\n🔍 STEP 2: Creating TOC-Based Chunks")
    print("=" * 60)
    
    # Create chunks using recommended strategy
    chunks_result = chunker.create_toc_based_chunks(doc_name, "recommended")
    
    print(f"✅ TOC-Based Chunking Complete:")
    print(f"   📦 Total chunks: {chunks_result['total_chunks']}")
    print(f"   📊 Strategy: {chunks_result['chunking_strategy']}")
    
    # Save results
    with open("chunks_2025-01-31/toc_analysis.json", "w") as f:
        json.dump(structure, f, indent=2)
    
    with open("chunks_2025-01-31/toc_chunks.json", "w") as f:
        json.dump(chunks_result, f, indent=2)
    
    with open("chunks_2025-01-31/toc_index.json", "w") as f:
        json.dump(chunks_result['index'], f, indent=2)
    
    # Create readable summary
    summary = []
    summary.append("# Table of Contents-Based Chunks\n")
    summary.append(f"**Document**: {doc_name}\n")
    summary.append(f"**Strategy**: {chunks_result['chunking_strategy']}\n")
    summary.append(f"**Total Chunks**: {chunks_result['total_chunks']}\n\n")
    
    summary.append("## Chunk Overview\n")
    for chunk in chunks_result['chunks']:
        hierarchy_path = f"{chunk['hierarchy']['section']} > {chunk['hierarchy']['subsection']} > {chunk['hierarchy']['sub_subsection']}".replace(' > None', '')
        summary.append(f"**{chunk['section_number']}**: {chunk['title']}\n")
        summary.append(f"- Hierarchy: {hierarchy_path}\n")
        summary.append(f"- Words: {chunk['word_count']}\n")
        summary.append(f"- Sections included: {len(chunk['sections'])}\n")
        summary.append(f"- Preview: {chunk['content'][:200]}...\n\n")
    
    with open("chunks_2025-01-31/toc_chunks_summary.md", "w") as f:
        f.write(''.join(summary))
    
    print(f"\n📁 TOC Output Files Created:")
    print(f"   📋 toc_analysis.json - Full TOC structure analysis")
    print(f"   📦 toc_chunks.json - TOC-based chunks with metadata")
    print(f"   🗂️ toc_index.json - Search index by section numbers")
    print(f"   📖 toc_chunks_summary.md - Human-readable summary")

if __name__ == "__main__":
    main()