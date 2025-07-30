#!/usr/bin/env python3
"""
Simple L5X round-trip test script.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from crossplc.l5x2st import L5X2STConverter
from crossplc.st2l5x import convert_st_to_l5x_string

# Use a generic test file path - user should provide their own L5X file
L5X_FILE = "test_project.L5X"  # User should replace with actual file

def main():
    """Run the round-trip test."""
    if not os.path.exists(L5X_FILE):
        print(f"⚠️  File {L5X_FILE} not found. Skipping round-trip test.")
        print("   To run this test, provide a valid L5X file path.")
        return
    
    print(f"Testing round-trip conversion: {L5X_FILE}")
    
    try:
        # Step 1: L5X → ST
        print("Step 1: Converting L5X to ST...")
        l5x2st = L5X2STConverter()
        st_code = l5x2st.convert_l5x_to_st(L5X_FILE)
        
        # Save intermediate ST
        st_file = "roundtrip_intermediate.st"
        with open(st_file, 'w') as f:
            f.write(st_code)
        print(f"  Saved ST to: {st_file}")
        
        # Step 2: ST → L5X
        print("Step 2: Converting ST back to L5X...")
        l5x_xml = convert_st_to_l5x_string(st_code)
        
        # Save final L5X
        final_l5x = "roundtrip_final.L5X"
        with open(final_l5x, 'w') as f:
            f.write(l5x_xml)
        print(f"  Saved L5X to: {final_l5x}")
        
        print("✅ Round-trip conversion completed successfully!")
        print(f"   Original: {L5X_FILE}")
        print(f"   ST intermediate: {st_file}")
        print(f"   Final: {final_l5x}")
        
    except Exception as e:
        print(f"❌ Error during round-trip conversion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 