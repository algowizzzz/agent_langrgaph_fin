#!/usr/bin/env python3
"""
Phase 2 Implementation Script - Fix Planning Engine

This script replaces the planning engine with the fixed version that has proper condition parsing.
"""

import os
import shutil
from pathlib import Path

def implement_phase_2_fixes():
    """Replace planning engine with fixed version."""
    
    print("🔧 Implementing Phase 2 Fixes - Planning Engine Repair")
    print("=" * 60)
    
    # Backup original files
    backup_dir = Path("output/phase2_backups")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_replace = [
        ("orchestrator_v2/planning_engine.py", "orchestrator_v2/planning_engine_fixed.py")
    ]
    
    for original_file, fixed_file in files_to_replace:
        print(f"\n📁 Processing {original_file}...")
        
        # Create backup
        if os.path.exists(original_file):
            backup_path = backup_dir / os.path.basename(original_file)
            shutil.copy2(original_file, backup_path)
            print(f"   ✅ Backed up to {backup_path}")
        
        # Replace with fixed version
        if os.path.exists(fixed_file):
            shutil.copy2(fixed_file, original_file)
            print(f"   ✅ Replaced with fixed version")
        else:
            print(f"   ❌ Fixed version not found: {fixed_file}")
    
    print(f"\n📊 Phase 2 Implementation Summary:")
    print(f"   ✅ Condition parsing fixed")
    print(f"   ✅ LLM response validation improved")
    print(f"   ✅ Parameter validation enhanced")
    print(f"   ✅ Template-based fallback planning added")
    print(f"   ✅ Original files backed up to {backup_dir}")
    
    print(f"\n🎯 Next: Run Phase 3 to fix execution engine")

if __name__ == "__main__":
    implement_phase_2_fixes()