#!/usr/bin/env python3
"""
Create main sections only (1.1-1.10 + Annex 1-2)
"""

import json

# Load the full chunks
with open("chunks_2025-01-31/final_toc_chunks.json", "r") as f:
    full_data = json.load(f)

# Filter to only main sections (Level 1 and Level 2)
main_chunks = []
total_words = 0

for chunk in full_data['chunks']:
    if chunk['level'] in [1, 2]:  # Level 1 = Annexes, Level 2 = Main sections 1.1-1.10
        # Re-index the chunks
        chunk['chunk_index'] = len(main_chunks)
        main_chunks.append(chunk)
        total_words += chunk['word_count']

# Create filtered data
filtered_data = {
    'document': full_data['document'],
    'chunking_strategy': 'main_sections_only',
    'total_chunks': len(main_chunks),
    'total_words': total_words,
    'avg_words_per_chunk': total_words / len(main_chunks) if main_chunks else 0,
    'chunks': main_chunks,
    'section_breakdown': {
        'main_sections': [c for c in main_chunks if c['level'] == 2],
        'annexes': [c for c in main_chunks if c['level'] == 1]
    }
}

# Save filtered version
with open("chunks_2025-01-31/main_sections_only.json", "w") as f:
    json.dump(filtered_data, f, indent=2)

# Create summary
print("📊 MAIN SECTIONS ONLY - FILTERED RESULTS")
print("=" * 50)
print(f"✅ Total chunks: {len(main_chunks)}")
print(f"📝 Total words: {total_words:,}")
print(f"📈 Avg words/chunk: {total_words // len(main_chunks)}")

print(f"\n📋 Section Breakdown:")
print(f"   🔸 Main sections (1.1-1.10): {len([c for c in main_chunks if c['level'] == 2])}")
print(f"   🔸 Annexes: {len([c for c in main_chunks if c['level'] == 1])}")

print(f"\n📚 All 12 Chunks:")
for i, chunk in enumerate(main_chunks):
    print(f"   {i+1:2d}. {chunk['section_number']:8s} - {chunk['title'][:50]:<50} ({chunk['word_count']} words)")

print(f"\n✅ Saved to: chunks_2025-01-31/main_sections_only.json")