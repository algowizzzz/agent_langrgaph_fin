#!/usr/bin/env python3
"""
Apply All V2 Fixes Script

This script applies all the phased fixes to the orchestrator v2 system.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_phase_script(script_name: str):
    """Run a phase implementation script."""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd="output")
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Error running {script_name}:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Exception running {script_name}: {e}")
        return False

def apply_all_fixes():
    """Apply all phases of fixes to orchestrator v2."""
    
    print("🚀 APPLYING ALL ORCHESTRATOR V2 FIXES")
    print("=" * 60)
    
    # Phase 1: Mock Response Removal
    print("\n🔥 PHASE 1: Mock Response Removal")
    if not run_phase_script("PHASE_1_IMPLEMENTATION_SCRIPT.py"):
        print("❌ Phase 1 failed. Stopping.")
        return False
    
    # Phase 2: Planning Engine Fixes
    print("\n⚙️ PHASE 2: Planning Engine Fixes") 
    if not run_phase_script("PHASE_2_IMPLEMENTATION_SCRIPT.py"):
        print("❌ Phase 2 failed. Stopping.")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📋 Summary of Changes:")
    print("   ✅ Phase 1: Removed all mock responses")
    print("   ✅ Phase 2: Fixed planning engine condition parsing")
    print("   ✅ Tools now return structured error information")
    print("   ✅ Planning engine handles LLM responses properly")
    print("   ✅ Parameter validation improved")
    
    print("\n🧪 Ready for Testing:")
    print("   Run the V2 coverage test again to verify improvements")
    print("   Expected: Higher tool execution rates")
    print("   Expected: Better error reporting")
    
    print("\n📁 Backups Created:")
    print("   Phase 1 backups: output/phase1_backups/")
    print("   Phase 2 backups: output/phase2_backups/")
    
    return True

if __name__ == "__main__":
    success = apply_all_fixes()
    if success:
        print("\n🎉 All fixes applied successfully!")
    else:
        print("\n💥 Fix application failed. Check errors above.")
        sys.exit(1)